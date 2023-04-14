## Kubeflow Roles Operator

### Overview
This charm encompasses the Kubernetes Python operator for Kubeflow Roles
(see [CharmHub](https://charmhub.io/?q=kubeflow-roles)).  

Implemented specifically in this charm are: 
* aggregation `ClusterRoles` used by Kubeflow to grant user access control, 
* application-specific `ClusterRoles` that cannot be implemented in their respective charm directly (for example, for pod spec charms)

### Kubeflow User Aggregation Roles

Kubeflow uses the concept of [user facing roles](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#user-facing-roles) to provide access control to users.  Kubeflow's instantiation of this pattern is described [here](https://github.com/kubeflow/manifests/tree/3e08dc102059def5a0b0d04560c7d119959bf506/common/kubeflow-roles).  The `ClusterRoles` Kubeflow implements are are:

* rbac.authorization.kubeflow.org/aggregate-to-kubeflow-view
* rbac.authorization.kubeflow.org/aggregate-to-kubeflow-edit
* rbac.authorization.kubeflow.org/aggregate-to-kubeflow-admin

These `ClusterRoles` ([see here](https://github.com/canonical/kubeflow-roles-operator/blob/d96c15e4de8bb36e9ec039ae66c12af1084ecd2b/src/manifests/kubeflow-roles.yaml#L4) for their definition in this charm) aggregate the permissions of all existing `ClusterRoles` that match a selector (in this case, `ClusterRoles` that have one of the `rbac.authorization.kubeflow.org/aggregate-to-kubeflow-*: "true"` labels), allowing permissions to be added to the aggregation roles without editing the roles themselves.  

Permissions aggregated into these `ClusterRoles` cover both standard Kubernetes resources (e.g. `Pods` and `Services`), such as defined in [this ClusterRole](https://github.com/canonical/kubeflow-roles-operator/blob/d96c15e4de8bb36e9ec039ae66c12af1084ecd2b/src/manifests/kubeflow-roles.yaml#L74), as well as any access to custom resources.  Applications in Kubeflow often add new `CustomResources` to the Kubernetes cluster that users must interact with, such as the `Notebook` object from the `notebook-controller`.  To grant user access to these custom resources, applications must [implement their own `ClusterRoles`](https://github.com/canonical/kubeflow-roles-operator/blob/afe3e1ea0a6dcb4136a506d4d2b697f9d1589a27/src/manifests/notebook-controller.yaml#L17) that, through the `label: rbac.authorization.kubeflow.org/aggregate-to-kubeflow-*` labels, are aggregate into the above described roles.  

To actually grant users the roles described in the aggregation `ClusterRoles`, Kubeflow's Profile Controller binds the above `view` and `edit` `ClusterRoles` to the `ServiceAccounts` of each user during the creation of profiles.  This provides users access to everything defined in any of aggregated `ClusterRoles`.

### Purposes of this Charm

#### Implementing the Aggregation `ClusterRoles`

The primary need for this charm is to implement the Kubeflow aggregation `ClusterRoles` as described above.  Examples of these roles as implemented in the upstream manifests are [here](https://github.com/kubeflow/manifests/blob/3e08dc102059def5a0b0d04560c7d119959bf506/common/kubeflow-roles/base/cluster-roles.yaml), where we have implemented our version [here](https://github.com/canonical/kubeflow-roles-operator/blob/afe3e1ea0a6dcb4136a506d4d2b697f9d1589a27/src/manifests/kubeflow-roles.yaml#L4).   These `ClusterRoles` do not naturally fit in any other charm and thus need a separate place for implementation.

#### Implementing some Application-Specific `ClusterRoles`

The secondary need for this charm is to be a place to implement any application-specific `ClusterRoles` for aggregation (such as, for the [notebook controller](https://github.com/canonical/kubeflow-roles-operator/blob/afe3e1ea0a6dcb4136a506d4d2b697f9d1589a27/src/manifests/notebook-controller.yaml#L17)) when it is impractical to implement those ClusterRoles in their parent charm.  For example, in charms where:

* the charm is implemented as a pod spec charm and thus cannot create a custom `ClusterRole`
* it is undesirable to create the ClusterRole in the other charm, perhaps because that would require `--trust`ing the charm

In these cases, those application-specific `ClusterRoles` are instead defined statically here.  

### Known Limitations/Concerns

* for deployments which do not use all components of Kubeflow (for example, a Kubeflow implementation that omits Pipelines), we still create RBAC for users to interact with the Pipeline's resources.  This could matter if an unrelated application on the cluster had similarly named resources
* implementing application-specific `ClusterRoles` in this manner effectively removes the benefit of their decentralized implementation in Kubeflow.  As is, any change in an application's `ClusterRole` will also require a change to this repo. 

## Install

To install Kubeflow Roles, run:

    juju deploy kubeflow-roles

For more information, see https://juju.is/docs

## Development

On migration of a Podspec charm to sidecar, you should move the application-specific `ClusterRoles` from this charm to the charm's Auth manifests. Sidecar charms can create a custom `ClusterRole`.
