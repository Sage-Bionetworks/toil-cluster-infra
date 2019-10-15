# toil-cluster-infra
Infrastructure for a Toil cluster (http://toil.ucsc-cgl.org) in AWS.

## Workflow
The workflow to provision AWS resources is done using pull requests.
Requests using PRs provide history, gating, reviewing and an approval
process.

## Contributions
Contributions are welcome.

Requirements:
* Install [pre-commit](https://pre-commit.com/#install) app
* Clone this repo
* Run `pre-commit install` to install the git hook.

## Linting
As a pre-deployment step we syntatically validate our sceptre and
cloudformation yaml files with [pre-commit](https://pre-commit.com).

Please install pre-commit. Once installed, the file validations will
automatically run on every commit. Alternatively you can manually
execute the validations by running `pre-commit run --all-files`.
