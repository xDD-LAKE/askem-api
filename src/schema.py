BASE_KEYWORD_PROPERTIES = [
        "ASKEM_ID",
        "ASKEM_CLASS",
        "EXTERNAL_URL",
        ]

BASE_OBJECT_PROPERTIES = [
        "RAW_DATA",
        ]

BASE_TEXT_PROPERTIES = [
        "DOMAIN_TAGS"
        ]

# Keyword for exact-match fields, including fields which are arrays of keywords
KEYWORD_PROPERTIES = [
        "functionNetwork",
        "hasParameter",
        "consideredModel",
        "DOI",
        "XDDID",
        "documentID",
        "sectionID",
        "sourceID",
        "allParameters",
        ]

# Text for fulltext querying
TEXT_PROPERTIES = [
        "description",
        "rawTime",
        "rawLocation",
        "populationMetadata",
        "title",
        "abstract",
        "documentTitle",
        "textContent",
        "contentText",
        "sectionTitle",
        "relevantSentences",
        "caption",
        "synonyms",
        "primaryName",
        ]

OBJECT_PROPERTIES = [
        "rawData",
        "contentJSON",
        "gromet",
        ]

# Float
NUMERICAL_PROPERTIES = ["value", "trustScore"]

# Integer
INTEGER_PROPERTIES = ["indexInDocument"]

# Binary
BINARY_PROPERTIES = ["image"]
# Nested
NESTED_PROPERTIES = []



