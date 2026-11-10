import re
from typing import Optional, Dict, Any
from app.models.schemas import CitizenProfile

class ProfileService:
    """Manages parsing, structuring, and merging citizen profiles."""

    @staticmethod
    def extract_from_natural_language(text: str) -> CitizenProfile:
        lower = text.lower()
        profile_data: Dict[str, Any] = {}

        # Age
        age_match = re.search(r"\b(\d{1,2})\s*(?:years? old|yo|yr|year)\b", lower)
        if age_match:
            profile_data["age"] = int(age_match.group(1))

        # Land
        land_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:acres?|hectares?|guntha)", lower)
        if land_match:
            profile_data["land_ownership_acres"] = float(land_match.group(1))

        # Income
        lakh_match = re.search(r"(?:rs\.?|₹|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs)", lower)
        if lakh_match:
            profile_data["annual_income"] = float(lakh_match.group(1)) * 100000
        else:
            per_month_match = re.search(r"(?:rs\.?|₹|inr)?\s*(\d{3,6})\s*(?:per month|/month|pm)", lower)
            if per_month_match:
                profile_data["monthly_income"] = float(per_month_match.group(1))

        # State
        states = [
            "Karnataka", "Maharashtra", "Tamil Nadu", "Kerala", "Telangana", "Andhra Pradesh",
            "Gujarat", "Rajasthan", "Uttar Pradesh", "Madhya Pradesh", "Bihar", "West Bengal",
            "Punjab", "Haryana", "Odisha", "Assam"
        ]
        for s in states:
            if s.lower() in lower:
                profile_data["state"] = s
                break

        # Occupation / Roles
        if any(w in lower for w in ["farmer", "farming", "cultivator", "agriculture", "kisan"]):
            profile_data["occupation"] = "Farmer"
            profile_data["is_farmer"] = True
        elif any(w in lower for w in ["student", "studying", "college", "school"]):
            profile_data["occupation"] = "Student"
            profile_data["is_student"] = True
        elif any(w in lower for w in ["vendor", "street vendor", "hawker", "construction worker", "labourer", "driver"]):
            profile_data["occupation"] = "Unorganized Worker"
        elif any(w in lower for w in ["business", "shop", "trader", "enterprise", "entrepreneur", "small unit"]):
            profile_data["occupation"] = "Micro Entrepreneur"

        # Categories
        if re.search(r"\b(sc|scheduled caste)\b", lower):
            profile_data["category"] = "SC"
        elif re.search(r"\b(st|scheduled tribe)\b", lower):
            profile_data["category"] = "ST"
        elif re.search(r"\b(obc|other backward class)\b", lower):
            profile_data["category"] = "OBC"

        return CitizenProfile(**profile_data)

    @staticmethod
    def combine_profiles(text_profile: CitizenProfile, form_profile: CitizenProfile) -> CitizenProfile:
        """Merges text-extracted profile with explicitly selected structured form fields."""
        return text_profile.merge_with(form_profile)
