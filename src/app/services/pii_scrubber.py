import re

class PIIScrubber:
    """
    Utility class to detect and mask Personally Identifiable Information (PII) 
    from user queries to comply with privacy and safety guidelines.
    """
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')

    # Normalized patterns (to run on alphanumeric-only text)
    PAN_NORM = re.compile(r'[A-Za-z]{5}\d{4}[A-Za-z]')
    AADHAAR_NORM = re.compile(r'\d{12}')
    PHONE_NORM = re.compile(r'(?:91)?[6-9]\d{9}')
    FOLIO_NORM = re.compile(r'\d{9,18}')

    # OTP Context Pattern: Matches keywords suggesting an OTP is present in the text
    OTP_CONTEXT_PATTERN = re.compile(r'\b(?:otp|code|pin|password|verification)\b', re.IGNORECASE)

    @classmethod
    def scrub_text(cls, text: str) -> str:
        """
        Scrub sensitive PII from the input string, replacing matches with placeholders.
        """
        if not text:
            return ""
            
        # 1. Scrub Email
        text = cls.EMAIL_PATTERN.sub("[MASKED_EMAIL]", text)
        
        # 2. Scrub OTP (only if context keywords like 'otp', 'code', etc. are present)
        if cls.OTP_CONTEXT_PATTERN.search(text):
            def otp_repl(match):
                val = match.group(0)
                # Ignore numbers that look like years (e.g. 1900 to 2100) to avoid false positives
                if len(val) == 4:
                    try:
                        num = int(val)
                        if 1900 <= num <= 2100:
                            return val
                    except ValueError:
                        pass
                return "[MASKED_OTP]"
            
            text = re.sub(r'\b\d{4,6}\b', otp_repl, text)
            
        # 3. Scrub PAN, Aadhaar, Phone, Folio using normalization and index mapping
        ignore_chars = set(" -./\\()[],;+")
        normalized = []
        orig_indices = []
        for i, char in enumerate(text):
            if char not in ignore_chars:
                normalized.append(char)
                orig_indices.append(i)
        
        norm_str = "".join(normalized)

        def is_alphanumeric(char: str) -> bool:
            return char.isalnum() or char == '_'

        def has_word_boundary_before(start: int) -> bool:
            if start == 0:
                return True
            return is_alphanumeric(text[start - 1]) != is_alphanumeric(text[start])

        def has_word_boundary_after(end: int) -> bool:
            if end == len(text):
                return True
            return is_alphanumeric(text[end - 1]) != is_alphanumeric(text[end])

        spans_to_mask = []

        # Find PAN
        for match in cls.PAN_NORM.finditer(norm_str):
            start_norm, end_norm = match.span()
            start_orig = orig_indices[start_norm]
            end_orig = orig_indices[end_norm - 1] + 1
            if has_word_boundary_before(start_orig) and has_word_boundary_after(end_orig):
                spans_to_mask.append((start_orig, end_orig, "[MASKED_PAN]"))

        # Find Aadhaar
        for match in cls.AADHAAR_NORM.finditer(norm_str):
            start_norm, end_norm = match.span()
            start_orig = orig_indices[start_norm]
            end_orig = orig_indices[end_norm - 1] + 1
            if has_word_boundary_before(start_orig) and has_word_boundary_after(end_orig):
                lower_text = text.lower()
                # Skip treating a 12-digit number as Aadhaar if there are folio/account/bank cues in the query
                # unless the word "aadhaar" is also explicitly present.
                if ("folio" in lower_text or "account" in lower_text or "bank" in lower_text) and "aadhaar" not in lower_text:
                    continue
                spans_to_mask.append((start_orig, end_orig, "[MASKED_AADHAAR]"))

        # Find Phone
        for match in cls.PHONE_NORM.finditer(norm_str):
            start_norm, end_norm = match.span()
            start_orig = orig_indices[start_norm]
            end_orig = orig_indices[end_norm - 1] + 1
            if has_word_boundary_before(start_orig) and has_word_boundary_after(end_orig):
                spans_to_mask.append((start_orig, end_orig, "[MASKED_PHONE]"))

        # Find Folio / Bank Account (9-18 digits)
        for match in cls.FOLIO_NORM.finditer(norm_str):
            start_norm, end_norm = match.span()
            match_len = end_norm - start_norm
            start_orig = orig_indices[start_norm]
            end_orig = orig_indices[end_norm - 1] + 1
            if has_word_boundary_before(start_orig) and has_word_boundary_after(end_orig):
                if match_len == 12:
                    lower_text = text.lower()
                    # Only treat a 12-digit number as a Folio if folio/account/bank cues exist
                    # and the word "aadhaar" is not present.
                    if ("folio" in lower_text or "account" in lower_text or "bank" in lower_text) and "aadhaar" not in lower_text:
                        spans_to_mask.append((start_orig, end_orig, "[MASKED_FOLIO]"))
                else:
                    spans_to_mask.append((start_orig, end_orig, "[MASKED_FOLIO]"))

        if spans_to_mask:
            # Priority definition for labels
            label_priority = {
                "[MASKED_PAN]": 4,
                "[MASKED_PHONE]": 3,
                "[MASKED_AADHAAR]": 2,
                "[MASKED_FOLIO]": 1
            }
            
            # Sort by span length descending, then priority descending
            spans_to_mask.sort(key=lambda x: (x[1] - x[0], label_priority[x[2]]), reverse=True)
            
            accepted_spans = []
            for start, end, label in spans_to_mask:
                # Check if this span is nested inside or overlaps with an already accepted span
                is_nested = False
                for acc_start, acc_end, acc_label in accepted_spans:
                    if start < acc_end and end > acc_start:
                        is_nested = True
                        break
                if not is_nested:
                    accepted_spans.append((start, end, label))

            # Apply replacements from right to left to keep indices correct
            accepted_spans.sort(key=lambda x: x[0], reverse=True)
            for start, end, label in accepted_spans:
                if label == "[MASKED_PHONE]" and start > 0 and text[start - 1] == "+":
                    start -= 1
                text = text[:start] + label + text[end:]

        return text
