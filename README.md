## Kubeflow Roles Operator

### Overview
This charm encompasses the Kubernetes Python operator for Kubeflow Roles
(see [CharmHub](https://charmhub.io/?q=kubeflow-roles)).  

Implemented specifically in this charm are: 
* aggregation `ClusterRole`s used by Kubeflow to grant user access control, 
* application-specific `ClusterRole`s that cannot be implemented in their respective charm directly (for example, for pod spec charms)

### Kubeflow User Aggregation Roles

Kubeflow defines three [aggregation `ClusterRole`s](https://github.com/canonical/kubeflow-roles-operator/blob/afe3e1ea0a6dcb4136a506d4d2b697f9d1589a27/src/manifests/kubeflow-roles.yaml#L4) for use when granting roles to user `ServiceAccount`s:

* rbac.authorization.kubeflow.org/aggregate-to-kubeflow-view
* rbac.authorization.kubeflow.org/aggregate-to-kubeflow-edit
* rbac.authorization.kubeflow.org/aggregate-to-kubeflow-admin

These are bound to `ServiceAccount`s during the creation of profiles, and user workloads (for example, the `Pod` of a `Notebook`) use these `ServiceAccount`s.  By default, [this](https://github.com/canonical/kubeflow-roles-operator/blob/afe3e1ea0a6dcb4136a506d4d2b697f9d1589a27/src/manifests/kubeflow-roles.yaml#L74) is how users are granted access both to Kubernetes primitives such as creating `Pod`s and `Service`s.

Applications in Kubeflow often add new `CustomResource`s to the Kubernetes cluster that users must also interact with, such as the `Notebook` object from the `notebook-controller`.  To grant users access to these new resources, applications must [implement additional `ClusterRole`s](https://github.com/canonical/kubeflow-roles-operator/blob/afe3e1ea0a6dcb4136a506d4d2b697f9d1589a27/src/manifests/notebook-controller.yaml#L17) that, through the `label: rbac.authorization.kubeflow.org/aggregate-to-kubeflow-*` labels will get aggregated into the roles bound to users.  

Additional information is available in the [upstream manifest repo](https://github.com/kubeflow/manifests/tree/3e08dc102059def5a0b0d04560c7d119959bf506/common/kubeflow-roles)

### Purposes of this Charm

#### Implementing the Aggregation `ClusterRole`s

The primary need for this charm is to implement the aggregation `ClusterRole`s ([upstream](https://github.com/kubeflow/manifests/blob/3e08dc102059def5a0b0d04560c7d119959bf506/common/kubeflow-roles/base/cluster-roles.yaml), [this repo's implementation](https://github.com/canonical/kubeflow-roles-operator/blob/afe3e1ea0a6dcb4136a506d4d2b697f9d1589a27/src/manifests/kubeflow-roles.yaml#L4).   These do not naturally fit in any other charm.

#### Implementing some Application-Specific `ClusterRole`s

The secondary need for this charm is to be a place to implement any application-specific `ClusterRole`s for aggregation (such as, for the [notebook controller](https://github.com/canonical/kubeflow-roles-operator/blob/afe3e1ea0a6dcb4136a506d4d2b697f9d1589a27/src/manifests/notebook-controller.yaml#L17)) when it is impractical to implement those ClusterRoles in their parent charm.  For example, in charms where:

* the charm is implemented as a pod spec charm and thus cannot create a custom `ClusterRole`
* it is undesirable to create the ClusterRole in the other charm, perhaps because that would require `--trust`ing the charm

In these cases, those application-specific `ClusterRole`s are instead defined statically here.  

### Known Limitations/Concerns

* for deployments which do not use all components of Kubeflow (for example, a Kubeflow implementation that omits Pipelines), we still create RBAC for users to interact with the Pipeline's resources.  This could matter if an unrelated application on the cluster had similarly named resources
* implementing application-specific `ClusterRole`s in this manner effectively removes the benefit of their decentralized implementation in Kubeflow.  As is, any change in an application's `ClusterRole` will also require a change to this repo. 

## Install

To install Kubeflow Roles, run:

    juju deploy kubeflow-roles

For more information, see https://juju.is/docs
