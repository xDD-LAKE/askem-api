helptext = {
        "create" : {
            "description": "Create and register a new ASKEM-ID.",
            "options" : {
                "parameters" : {
                    "api_key" : "(required) API key assigned to an ASKEM-ID registrant. Can also be passed as a header in the 'x-api-key' field."
                    },
                "body" : "POSTed request body must be a JSON object of the form [json1, json2].",
                "methods" : ["POST"],
                "output_formats" : ["json"],
                "fields" : {
                    "registered_ids" : "Array of successfully registered ASKEM-IDs."
                    },
                "examples": []
                }
            },
        "object": {
            "description": "Retrieve or search (via metadata) for an uploaded object.",
            "options" : {
                "parameters": {
                    "object_id" : "Object id (ASKEM-ID) to retrieve. Optionally positional.",
                    "askem_class" : "TODO",
                    "domain_tag" : "TODO",
                    "doi" : "DOI of the document (or of the extractions' origin document)",
                    "TODO" : "TODO ASKEM_CLASS specific field parameter definitions.",
                },
                "methods" : ["GET"],
                "output_formats" : ["json"],
                "fields" : {
                    "ASKEM_CLASS" : "TODO",
                    "ASKEM_ID" : "Object id",
                    "_xdd_created" : "Timestamp of when the object was registered within xDD.",
                    "_xdd_registrant" : "Registrant of object within xDD.",
                    "properties": "TODO"
                    },
                "examples" : [
                    "/object/all",
                    "/object?source_title=CHIME",
                    ]
                }
            },
        "register" : {
            "description": "Register a location for a reserved ASKEM-ID.",
            "options" : {
                "parameters" : {
                    "api_key" : "(required) API key assigned to an ASKEM-ID registrant. Can also be passed as a header in the 'x-api-key' field."
                    },
                "body" : "POSTed request body must be a JSON object of the form [[ASKEM-ID, json], [ASKEM-ID, json]].",
                "methods" : ["POST"],
                "output_formats" : ["json"],
                "fields" : {
                    "registered_ids" : "List of successfully registered (or updated) ASKEM-IDs."
                    },
                "examples": []
                }
            },
        "reserve" : {
            "description": "Reserve a block of ASKEM-IDs for later registration.",
            "options" : {
                "parameters" : {
                    "api_key" : "(required) API key assigned to an ASKEM-ID registrant. Can also be passed as a header in the 'x-api-key' field.",
                    "n" : "(option, int, default 10) Number of ASKEM-IDs to reserve."
                    },
                "methods" : ["POST"],
                "output_formats" : ["json"],
                "fields" : {
                    "reserved_ids" : "List of unique ASKEM-IDs reserved for usage by the associated registrant API key."
                    },
                "examples": []
                }
            },
        }

