```bash
export API_KEY='PASTE_KEY_HERE'

curl --location --request POST 'xdddev.chtc.io/askem/create' \
	--header 'x-api-key: '"$API_KEY" \
	--header 'Content-Type: application/json' \
	--data-raw '{
	"data": "xyz",
	"metadata": {
		"documents": {
			"bibjson": {
				"title" : "Some Fake Articles"
			}
		}
	}
}'


# Response:
 {"success":{"v":1,"data":{"success":{"registered_ids":["6990cb0e-70e6-44bf-a588-981b6ac5095b"]}},"license":"https://creativecommons.org/licenses/by-nc/2.0/"}}

# Example retrieval
curl --location --request GET 'xdddev.chtc.io/askem/object/6990cb0e-70e6-44bf-a588-981b6ac5095b'
# Reponse:
{
"success": {
	"v": 1,
	"data": [
		{
			"data": "xyz",
			"metadata": {
				"documents": {
					"bibjson": {
						"title": "Some Fake Articles"
					}
				}
			},
			"askem_id": "6990cb0e-70e6-44bf-a588-981b6ac5095b",
			"_xdd_created": "2022-09-01T13:04:28.601011",
			"_xdd_registrant": 1
		}
	],
	"license": "https://creativecommons.org/licenses/by-nc/2.0/"
	}
}

# Example - querying by source document title
curl --location --request GET 'xdddev.chtc.io/askem/object?source_title=Fake'

# Reponse:
{
"success": {
	"v": 1,
	"data": [
		{
			"data": "xyz",
			"metadata": {
				"documents": {
					"bibjson": {
						"title": "Some Fake Articles"
					}
				}
			},
			"askem_id": "6990cb0e-70e6-44bf-a588-981b6ac5095b",
			"_xdd_created": "2022-09-01T13:04:28.601011",
			"_xdd_registrant": 1
		}
	],
	"license": "https://creativecommons.org/licenses/by-nc/2.0/"
	}
}
