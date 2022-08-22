# xDD sets API

- An API used to provide information and routing paths for a user or a machine interacting with xDD sets

## Quick first pass
For now:
- `sets` and `products` are hardcoded as json objects within respective dirs.
- Deployment will be in k8s and will auto-deploy whenever master branch updates.
- Product APIs will be _totally separate_. Long-term, it would be nice to fold this all together with a plugin system, but...baby steps.


## TODO:
- [ ] Live stats on /sets/<set_name> pages
- [ ] Store set definitions, etc. in a database.


## Objective
- /sets -- provides an overview of the available sets within xdd (maybe a straight duplicate of xddapi/sets?all )
- /sets/<set_name> -- overview for a particular set. Description, definition, statistics, available products
- /sets/<set_name>/<product_name> - overview of a type of product available for a set. Citation, description, external links
- /set/<set_name>/<product_name>/api - Outside of this API at the moment, but set+product specific APIs (e.g. cosmos API for the covid set)
