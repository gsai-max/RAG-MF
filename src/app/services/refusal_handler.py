from typing import TypedDict

class RefusalResponse(TypedDict):
    answer: str
    citation_url: str
    last_updated: str
    is_refusal: bool
    disclaimer: str

class RefusalHandler:
    """
    Handler to generate standardized compliance-friendly refusal responses
    incorporating SEBI and AMFI links when queries violate the facts-only constraint.
    """
    
    AMFI_URL = "https://www.amfiindia.com/"
    SEBI_URL = "https://investor.sebi.gov.in/"
    
    @classmethod
    def get_refusal(cls, intent: str, last_updated: str = "N/A") -> RefusalResponse:
        """
        Generate refusal payload based on classified intent.
        """
        disclaimer = "Facts-only. No investment advice."
        
        if intent == "advisory":
            answer = (
                "I am a facts-only assistant and cannot provide investment advice, "
                "opinions, or recommendations on whether to buy, sell, or hold mutual funds. "
                "I can only retrieve factual details from my defined corpus."
            )
            citation_url = cls.SEBI_URL
            
        elif intent == "comparison":
            answer = (
                "I am a facts-only assistant and do not compare mutual fund schemes "
                "or suggest which fund is better. For factual data, please query each scheme's "
                "details separately."
            )
            citation_url = cls.AMFI_URL
            
        elif intent == "speculative":
            answer = (
                "I cannot calculate expected future returns, project future values, "
                "or run financial calculators. I only retrieve factual, historical data "
                "from the source pages."
            )
            citation_url = cls.AMFI_URL
            
        else: # out_of_scope
            answer = (
                "The requested topic or fund is outside the scope of my database. "
                "I am limited to retrieving objective facts for the 110 ICICI Prudential "
                "Mutual Fund schemes in my defined corpus."
            )
            citation_url = cls.AMFI_URL
            
        return {
            "answer": answer,
            "citation_url": citation_url,
            "last_updated": last_updated,
            "is_refusal": True,
            "disclaimer": disclaimer
        }
