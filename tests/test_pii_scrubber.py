from src.app.services.pii_scrubber import PIIScrubber

def test_scrub_pan():
    text = "My PAN is ABCDE1234F."
    scrubbed = PIIScrubber.scrub_text(text)
    assert "[MASKED_PAN]" in scrubbed
    assert "ABCDE1234F" not in scrubbed

def test_scrub_aadhaar():
    text = "Here is my Aadhaar: 1234-5678-9012"
    assert "[MASKED_AADHAAR]" in PIIScrubber.scrub_text(text)
    
    text2 = "Aadhaar number 1234 5678 9012"
    assert "[MASKED_AADHAAR]" in PIIScrubber.scrub_text(text2)
    
    text3 = "No spaces Aadhaar 123456789012"
    assert "[MASKED_AADHAAR]" in PIIScrubber.scrub_text(text3)

def test_scrub_email():
    text = "Send info to user@example.com please."
    scrubbed = PIIScrubber.scrub_text(text)
    assert "[MASKED_EMAIL]" in scrubbed
    assert "user@example.com" not in scrubbed

def test_scrub_phone():
    text = "Call me at +91 9876543210 or 9876543210."
    scrubbed = PIIScrubber.scrub_text(text)
    assert "[MASKED_PHONE]" in scrubbed
    assert "9876543210" not in scrubbed

def test_scrub_otp():
    text = "Your OTP pin is 123456."
    scrubbed = PIIScrubber.scrub_text(text)
    assert "[MASKED_OTP]" in scrubbed
    assert "123456" not in scrubbed
    
    # Verify it does not scrub years like 2026 even with otp context keywords nearby
    text2 = "What was the performance of the fund in year 2026? Here is your verification code: 9876."
    scrubbed2 = PIIScrubber.scrub_text(text2)
    assert "2026" in scrubbed2
    assert "[MASKED_OTP]" in scrubbed2
    assert "9876" not in scrubbed2

def test_scrub_obfuscated_pan_phone_folio():
    # Obfuscated PAN
    text1 = "My PAN is ABCDE 1234 F"
    assert "[MASKED_PAN]" in PIIScrubber.scrub_text(text1)
    
    # Obfuscated Phone
    text2 = "Call me at +91 99-88-77-66-55"
    assert "[MASKED_PHONE]" in PIIScrubber.scrub_text(text2)

    # Contiguous 9-18 digit folio / bank account sequence
    text3 = "My folio number is 12345678901234"
    assert "[MASKED_FOLIO]" in PIIScrubber.scrub_text(text3)

    # Phone obfuscated with dots, slashes, parentheses
    text4 = "Call me at +91 99.88/77-66(55)"
    assert "[MASKED_PHONE]" in PIIScrubber.scrub_text(text4)

    # Folio obfuscated with brackets and spaces
    text5 = "Folio is [123-456-789-012]"
    assert "[MASKED_FOLIO]" in PIIScrubber.scrub_text(text5)
