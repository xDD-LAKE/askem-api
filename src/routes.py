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
                    "metadata_type" : "Type/source of metadata. Examples: [gromet_creation, textual_document_collection]",
                    "source_title" : "Title of document providing metadata. title field within documents.bibjson for metadata_type=textual_document_collection",
                    "provenance_method" : "The inference method (with version) used to derive data. Examples: [skema_code2fn_program_analysis]",
                },
                "methods" : ["GET"],
                "output_formats" : ["json"],
                "fields" : {
                    "metadata" : "Metadata of the stored object. Provided at ingestion by registrant and potentially augmented by additional processes.",
                    "askem_id" : "Object id",
                    "_xdd_created" : "Timestamp of when the object was registered within xDD.",
                    "_xdd_registrant" : "Registrant of object within xDD.",
                    "[object-specific fields]": "Provided at ingestion by registrant."
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
        "update" : {"TODO" : ""}
        }

