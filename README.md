# toil-cluster-infra
Infrastructure for a Toil cluster (http://toil.ucsc-cgl.org) in AWS.

## Provisioning
Provisioning a new cluster in AWS is done using pull requests.
Requests using PRs provide history, gating, reviewing and an approval process.

A Toil Cluster requires use of the following templates, some of which are
interdependent:
* toil-cluster-role-and-policy.yaml: creates policies, role, instance profile for use by EC2 instances
* toil-infra-essentials.yaml: creates a AWS KMS Key
* toil-instance.yaml: Creates the jumpbox EC2 instance with Toil installed. This instance is configured to run a toil launch-cluster command as a sysv service. The cluster is launched on jumpbox startup, and torn down when the jumpbox is stopped or terminated.

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

## Working with the Cluster

### Reaching the Jumpbox
In the AWS Console, find the jumpbox instance, and ssh it to using the PEM
that was specified in the stack creation. For example,
`ssh -i "toil.pem" ubuntu@10.23.95.18`.

### Reaching the Leader
Once you're on the Jumpbox, use this command to reach the cluster's leader,
where zone is the zone where you created the jumpbox and leader and you
specify the cluster name, for example, "rna-seq-reprocessing-toil-cluster-v001":
`sudo toil ssh-cluster --zone us-east-1c rna-seq-reprocessing-toil-cluster-v001`

### Setting up the Leader
The leader requires a little setup. Our typical workflow is to update, install
a few utilities, checkout the source code, and place the synapse configuration file.

```
# Update and Install
apt-get update
apt-get install -y git vim

# Check out the project and switch to the relevant branch and location,
# for example:

mkdir ~/jobs && cd $_
git clone https://github.com/Sage-Bionetworks/amp-workflows.git
git checkout wpoehlmdev
cd amp-workflows/amp-rnaseq_reprocessing/amp-rnaseq_reprocess-workflow/

# Do any other necessary setup -- for example, add a .synapseConfig file
mkdir /etc/synapse
vi /etc/synapse/.synapseConfig

# Finally, run the job! In the example from the repository mentioned above,
# we have a job-runner script:
nohup ./run-toil.py jobs/test-main-paired &
```

### Running a Toil Job on the Cluster
See the Toil documentation on running workflows generally and
[CWL](https://toil.readthedocs.io/en/latest/running/cwl.html?highlight=toil%20cwl%20runner)
in particular; also, see the Toil documentation on
[running a workflow in AWS](https://toil.readthedocs.io/en/latest/gettingStarted/quickStart.html#awscwl).

The repository in the example above uses a [custom script](https://raw.githubusercontent.com/Sage-Bionetworks/amp-workflows/4e94f1fc1e3035e97b1b633565d71d496a072a20/amp-rnaseq_reprocessing/amp-rnaseq_reprocess-workflow/run-toil.py) to start a job.
See the [readme](https://raw.githubusercontent.com/Sage-Bionetworks/amp-workflows/4e94f1fc1e3035e97b1b633565d71d496a072a20/amp-rnaseq_reprocessing/amp-rnaseq_reprocess-workflow/README.md) for more information on how to use that script.

## Troubleshooting

### Bucket Versioning
There appears to be a Toil bug that arises if a job is interrupted early. If one
restarts the job with the same jobstore, there is a warning about bucket
versioning.

### No capacity
If we keep getting `InsufficientInstanceCapacity` errors, here is the workflow.
If you're not in a hurry, just use fewer nodes. But in the common case where
there is some sort of deadline, there are workarounds.

#### Try another instance type
The easiest thing can be to try another instance type -- if you can adapt the
resource requirements specified in your workflow to use a different instance
type. AWS will tell you that the smartest thing to do is to use spot fleets for
diversity -- unfortunately, toil does not support this. Toil does support
listing multiple instance types, but the logic for matching a job to an instance
type is such that toil maps jobs to single instance types. So it won't try to
fit the job to another instance type, so it will never request the other type.

#### Use incremental capacity reservations
If you have the permissions, make a capacity reservation for what you want.
There is a capacity reservation utility in this repository.
If AWS rejects the reservation because capacity is insufficient, gradually dial down
the number of nodes you are requesting until you get a fulfilled request. If
what you can get is acceptable, start the job with this. You can then
periodically submit additional capacity reservations to reserve more capacity.
If you can manage to get another, then you can stop the job and restart with
the capacity in the original fulfilled request plus the additional capacity
acquired.
