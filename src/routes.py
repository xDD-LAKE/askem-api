helptext = {
        "create" : {
            "description": "Create and register a new ASKE-ID.",
            "options" : {
                "parameters" : {
                    "api_key" : "(required) API key assigned to an ASKE-ID registrant. Can also be passed as a header in the 'x-api-key' field."
                    },
                "body" : "POSTed request body must be a JSON object of the form [json1, json2].",
                "methods" : ["POST"],
                "output_formats" : ["json"],
                "fields" : {
                    "registered_ids" : "Array of successfully registered ASKE-IDs."
                    },
                "examples": []
                }
            },
        "reserve" : {
            "description": "Reserve a block of ASKE-IDs for later registration.",
            "options" : {
                "parameters" : {
                    "api_key" : "(required) API key assigned to an ASKE-ID registrant. Can also be passed as a header in the 'x-api-key' field.",
                    "n" : "(option, int, default 10) Number of ASKE-IDs to reserve."
                    },
                "methods" : ["POST"],
                "output_formats" : ["json"],
                "fields" : {
                    "reserved_ids" : "List of unique ASKE-IDs reserved for usage by the associated registrant API key."
                    },
                "examples": []
                }
            },
        "object": {
            "description": "TODO"
            },
        "register" : {
            "description": "Register a location for a reserved ASKE-ID.",
            "options" : {
                "parameters" : {
                    "api_key" : "(required) API key assigned to an ASKE-ID registrant. Can also be passed as a header in the 'x-api-key' field."
                    },
                "body" : "POSTed request body must be a JSON object of the form [[ASKE-ID, json], [ASKE-ID, json]].",
                "methods" : ["POST"],
                "output_formats" : ["json"],
                "fields" : {
                    "registered_ids" : "List of successfully registered (or updated) ASKE-IDs."
                    },
                "examples": []
                }
            }
        }

