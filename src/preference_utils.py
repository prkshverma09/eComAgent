#!/usr/bin/env python3
"""
Preference Utilities for Consumer Shopping Agent

Shared utilities for handling user shopping preferences.
Used by both the consumer_preference_agent and consumer_mcp_server.
"""

import re
from typing import Dict, List, Tuple, Optional, Any


# ========================================
# Preference Schema
# ========================================
PREFERENCE_SCHEMA = {
    "shoe_size": {
        "type": "str",
        "description": "User's shoe size (e.g., '10', '10.5', 'M10/W12')",
        "examples": ["10", "10.5", "M10/W12", "UK 9"]
    },
    "max_budget": {
        "type": "float",
        "description": "Maximum budget in GBP",
        "examples": [100, 150, 200, 250]
    },
    "min_budget": {
        "type": "float",
        "description": "Minimum budget in GBP",
        "examples": [50, 75, 100]
    },
    "preferred_colors": {
        "type": "list",
        "description": "Preferred shoe colors",
        "examples": [["black", "gray"], ["white", "blue"], ["multi"]]
    },
    "preferred_brands": {
        "type": "list",
        "description": "Preferred brands from catalog",
        "valid_values": [
            "AeroStride", "CloudTrail", "FleetStep", "NimbusPath",
            "NovaStride", "PulseTrack", "RoadRift", "TerraSprint",
            "UrbanTempo", "VelociRun"
        ]
    },
    "preferred_type": {
        "type": "str",
        "description": "Preferred shoe type",
        "valid_values": ["Trail", "Road", "Road fast", "Road race"]
    },
    "gender": {
        "type": "str",
        "description": "Target gender for shoes",
        "valid_values": ["Men", "Women", "Men and Women"]
    },
    "features": {
        "type": "list",
        "description": "Desired shoe features",
        "valid_values": ["Wide fit", "Arch Support", "Waterproof", "Lightweight"]
    },
    "season": {
        "type": "str",
        "description": "Preferred season/usage",
        "valid_values": ["Summer", "Winter", "All-season", "Spring/Summer", "Trail", "Race"]
    }
}


# ========================================
# Color Mappings
# ========================================
COLOR_SYNONYMS = {
    "grey": "gray",
    "dark": "black",
    "neutral": ["black", "gray", "navy"],
    "bright": ["red", "multi"],
    "colorful": "multi"
}

VALID_COLORS = ["black", "white", "gray", "navy", "blue", "red", "green", "multi", "limited"]


# ========================================
# Natural Language Parsing
# ========================================
def parse_preference_from_text(text: str) -> Tuple[Optional[str], Optional[Any]]:
    """
    Parse natural language text to extract preference key-value pairs.

    Args:
        text: Natural language input (e.g., "my size is 10")

    Returns:
        Tuple of (preference_key, value) or (None, None) if not parseable
    """
    text_lower = text.lower().strip()

    # Size patterns
    size_patterns = [
        r'size\s*(?:is\s*)?(\d+(?:\.\d+)?)',
        r'(?:uk|us|eu)\s*(?:size\s*)?(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*(?:uk|us|eu)',
        r'i\s*(?:am|wear)\s*(?:a\s*)?(?:size\s*)?(\d+(?:\.\d+)?)'
    ]
    for pattern in size_patterns:
        match = re.search(pattern, text_lower)
        if match:
            return ("shoe_size", match.group(1))

    # Budget patterns
    budget_patterns = [
        r'budget\s*(?:is\s*)?[£$]?\s*(\d+(?:\.\d+)?)',
        r'under\s*[£$]?\s*(\d+(?:\.\d+)?)',
        r'(?:max|maximum)\s*[£$]?\s*(\d+(?:\.\d+)?)',
        r'(?:up\s*to|no\s*more\s*than)\s*[£$]?\s*(\d+(?:\.\d+)?)',
        r'[£$]\s*(\d+(?:\.\d+)?)\s*(?:or\s*less|max)',
        r'spend\s*(?:up\s*to\s*)?[£$]?\s*(\d+(?:\.\d+)?)'
    ]
    for pattern in budget_patterns:
        match = re.search(pattern, text_lower)
        if match:
            return ("max_budget", float(match.group(1)))

    # Color patterns
    found_colors = []
    for color in VALID_COLORS:
        if color in text_lower:
            found_colors.append(color)
    # Check synonyms
    for synonym, mapped in COLOR_SYNONYMS.items():
        if synonym in text_lower:
            if isinstance(mapped, list):
                found_colors.extend(mapped)
            else:
                found_colors.append(mapped)
    if found_colors:
        return ("preferred_colors", list(set(found_colors)))

    # Type patterns
    type_mappings = {
        "trail": "Trail",
        "road": "Road",
        "race": "Road race",
        "racing": "Road fast",
        "fast": "Road fast",
        "marathon": "Road",
        "daily trainer": "Road",
        "daily": "Road"
    }
    for keyword, type_val in type_mappings.items():
        if keyword in text_lower:
            return ("preferred_type", type_val)

    # Brand patterns
    brands = PREFERENCE_SCHEMA["preferred_brands"]["valid_values"]
    found_brands = [b for b in brands if b.lower() in text_lower]
    if found_brands:
        return ("preferred_brands", found_brands)

    # Gender patterns
    if any(w in text_lower for w in ["women", "female", "ladies", "womens"]):
        return ("gender", "Women")
    elif any(w in text_lower for w in ["men", "male", "mens"]) and "women" not in text_lower:
        return ("gender", "Men")
    elif "unisex" in text_lower:
        return ("gender", "Men and Women")

    # Season patterns
    if "summer" in text_lower:
        return ("season", "Summer")
    elif "winter" in text_lower:
        return ("season", "Winter")
    elif "all-season" in text_lower or "year-round" in text_lower or "all season" in text_lower:
        return ("season", "All-season")

    # Feature patterns
    features = []
    if "wide" in text_lower or "wide fit" in text_lower:
        features.append("Wide fit")
    if "arch" in text_lower or "arch support" in text_lower:
        features.append("Arch Support")
    if "waterproof" in text_lower or "water proof" in text_lower:
        features.append("Waterproof")
    if "lightweight" in text_lower or "light weight" in text_lower or "light" in text_lower:
        features.append("Lightweight")
    if features:
        return ("features", features)

    return (None, None)


def parse_multiple_preferences(text: str) -> Dict[str, Any]:
    """
    Parse text that might contain multiple preferences.

    Args:
        text: Natural language input with potentially multiple preferences

    Returns:
        Dictionary of extracted preferences
    """
    preferences = {}

    # Split by common separators and parse each part
    parts = re.split(r'[,;]|\band\b|\balso\b', text)

    for part in parts:
        key, value = parse_preference_from_text(part.strip())
        if key and value:
            # Merge list values
            if key in preferences and isinstance(value, list):
                existing = preferences[key]
                if isinstance(existing, list):
                    preferences[key] = list(set(existing + value))
                else:
                    preferences[key] = value
            else:
                preferences[key] = value

    # If no parts parsed, try the whole text
    if not preferences:
        key, value = parse_preference_from_text(text)
        if key and value:
            preferences[key] = value

    return preferences


# ========================================
# Query Enhancement
# ========================================
def enhance_query_with_preferences(base_query: str, preferences: Dict[str, Any]) -> str:
    """
    Enhance a product search query with user preferences.

    Args:
        base_query: Original search query
        preferences: User's saved preferences

    Returns:
        Enhanced query string
    """
    enhancements = []

    # Add shoe type
    if preferences.get("preferred_type"):
        ptype = preferences["preferred_type"]
        if ptype.lower() not in base_query.lower():
            enhancements.append(ptype)

    # Add budget constraint
    if preferences.get("max_budget"):
        budget = preferences["max_budget"]
        if "under" not in base_query.lower() and "£" not in base_query:
            enhancements.append(f"under £{int(budget)}")

    # Add gender
    if preferences.get("gender"):
        gender = preferences["gender"]
        if gender.lower() not in base_query.lower():
            enhancements.append(f"for {gender}")

    # Add season
    if preferences.get("season"):
        season = preferences["season"]
        if season.lower() not in base_query.lower():
            enhancements.append(season)

    # Add colors (limit to 2)
    if preferences.get("preferred_colors"):
        colors = preferences["preferred_colors"]
        if isinstance(colors, list) and colors:
            color_str = ", ".join(colors[:2])
            if not any(c in base_query.lower() for c in colors):
                enhancements.append(f"in {color_str}")

    # Add features (limit to 2)
    if preferences.get("features"):
        features = preferences["features"]
        if isinstance(features, list):
            for feature in features[:2]:
                if feature.lower() not in base_query.lower():
                    enhancements.append(feature)

    # Combine query
    if enhancements:
        return f"{base_query} {' '.join(enhancements)}".strip()
    return base_query


def build_filter_dict(preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a filter dictionary for database queries from preferences.

    Args:
        preferences: User's saved preferences

    Returns:
        Filter dictionary compatible with vector store queries
    """
    filters = {}

    if preferences.get("preferred_type"):
        filters["Type"] = preferences["preferred_type"]

    if preferences.get("gender"):
        filters["Gender"] = preferences["gender"]

    if preferences.get("season"):
        filters["Season"] = preferences["season"]

    if preferences.get("max_budget"):
        filters["max_price"] = preferences["max_budget"]

    if preferences.get("min_budget"):
        filters["min_price"] = preferences["min_budget"]

    if preferences.get("preferred_brands"):
        brands = preferences["preferred_brands"]
        if isinstance(brands, list) and len(brands) == 1:
            filters["Brand"] = brands[0]
        # Multiple brands would need OR logic in query

    return filters


# ========================================
# Formatting
# ========================================
def format_preferences_display(preferences: Dict[str, Any]) -> str:
    """
    Format preferences for human-readable display.

    Args:
        preferences: User's preferences dictionary

    Returns:
        Formatted string for display
    """
    if not preferences:
        return "No preferences saved."

    labels = {
        "shoe_size": "Shoe Size",
        "max_budget": "Max Budget",
        "min_budget": "Min Budget",
        "preferred_colors": "Preferred Colors",
        "preferred_brands": "Preferred Brands",
        "preferred_type": "Shoe Type",
        "gender": "Gender",
        "features": "Features",
        "season": "Season"
    }

    lines = []
    for key, value in preferences.items():
        label = labels.get(key, key.replace("_", " ").title())

        if isinstance(value, list):
            display_value = ", ".join(value) if value else "Not set"
        elif key in ["max_budget", "min_budget"] and value:
            display_value = f"£{value}"
        elif value:
            display_value = str(value)
        else:
            continue

        lines.append(f"- {label}: {display_value}")

    return "\n".join(lines) if lines else "No preferences saved."


def preferences_to_summary(preferences: Dict[str, Any]) -> str:
    """
    Create a brief summary of preferences for LLM context.

    Args:
        preferences: User's preferences dictionary

    Returns:
        Brief summary string
    """
    parts = []

    if preferences.get("shoe_size"):
        parts.append(f"size {preferences['shoe_size']}")

    if preferences.get("max_budget"):
        parts.append(f"budget under £{int(preferences['max_budget'])}")

    if preferences.get("preferred_type"):
        parts.append(f"{preferences['preferred_type'].lower()} shoes")

    if preferences.get("gender"):
        parts.append(f"for {preferences['gender'].lower()}")

    if preferences.get("preferred_colors"):
        colors = preferences["preferred_colors"]
        if isinstance(colors, list) and colors:
            parts.append(f"in {', '.join(colors[:2])}")

    if preferences.get("preferred_brands"):
        brands = preferences["preferred_brands"]
        if isinstance(brands, list) and brands:
            parts.append(f"preferring {', '.join(brands[:2])}")

    if parts:
        return f"User wants: {', '.join(parts)}"
    return "No specific preferences"


# ========================================
# Validation
# ========================================
def validate_preference(key: str, value: Any) -> Tuple[bool, str]:
    """
    Validate a preference value against the schema.

    Args:
        key: Preference key
        value: Value to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if key not in PREFERENCE_SCHEMA:
        return True, ""  # Allow unknown keys

    schema = PREFERENCE_SCHEMA[key]
    expected_type = schema["type"]

    # Type validation
    if expected_type == "float":
        try:
            float(value)
        except (ValueError, TypeError):
            return False, f"{key} must be a number"

    elif expected_type == "list":
        if not isinstance(value, list):
            return False, f"{key} must be a list"

    # Value validation
    if "valid_values" in schema and value:
        valid = schema["valid_values"]
        if isinstance(value, list):
            invalid = [v for v in value if v not in valid]
            if invalid:
                return False, f"Invalid values for {key}: {invalid}. Valid: {valid}"
        elif value not in valid:
            return False, f"Invalid {key}: {value}. Valid: {valid}"

    return True, ""


def get_preference_help() -> str:
    """Get help text for available preferences."""
    lines = ["**Available Preferences:**\n"]

    for key, schema in PREFERENCE_SCHEMA.items():
        desc = schema["description"]
        lines.append(f"- **{key}**: {desc}")

        if "valid_values" in schema:
            lines.append(f"  Valid values: {', '.join(schema['valid_values'])}")
        elif "examples" in schema:
            examples = schema["examples"]
            if isinstance(examples[0], list):
                examples = [str(e) for e in examples]
            lines.append(f"  Examples: {', '.join(str(e) for e in examples[:3])}")

    return "\n".join(lines)
