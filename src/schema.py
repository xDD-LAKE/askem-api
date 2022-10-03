BASE_KEYWORD_PROPERTIES = [
        "ASKEM_ID",
        "ASKEM_CLASS",
        "DOMAIN_TAGS",
        "EXTERNAL_URL",
        ]

BASE_OBJECT_PROPERTIES = [
        "RAW_DATA"
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
        "sectionTitle",
        "relevantSentences",
        "caption",
        "synonyms",
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

# Nested
NESTED_PROPERTIES = []



