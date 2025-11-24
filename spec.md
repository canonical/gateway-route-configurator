|                                                      Index                                                     | ISD259                                                         |
| :------------------------------------------------------------------------------------------------------------: | -------------------------------------------------------------- |
|                                                    **Title**                                                   | gateway-route integration and Gateway Route Configurator charm |
| [**Status**](https://docs.google.com/document/d/1lStJjBGW7lyojgBhxGLUNnliUocYWjAZ1VEbbVduX54/edit?usp=sharing) |  Drafting                                                      |
|                                                   **Authors**                                                  |  [Ali Ugur](mailto:ali.ugur@canonical.com)                     |
|  [**Type**](https://docs.google.com/document/d/1lStJjBGW7lyojgBhxGLUNnliUocYWjAZ1VEbbVduX54/edit?usp=sharing)  |  Implementation                                                |
|                                                   **Created**                                                  |  2025-11-10                                                    |


# Abstract

Currently, the Gateway API Integrator charm only supports the generic ingress integration, which only covers the most basic use cases. In many cases we found out that our users want to serve their applications in their own specific domains, which is not supported with the current ingress integration and Gateway API Integrator. In response to that, this spec proposes a gateway-route integration to support this use case. Since most of the charms in deployment are using ingress integration, the spec also proposes a configurator charm called Gateway Route Configurator, which will relate to the workload charm through ingress integration and to the Gateway API Integrator charm through the new gateway-route integration.

This spec defines the gateway-route integration and the Gateway Route Configurator charm. This integration will be a minimal implementation of the gateway API, which only covers paths, hostname and hosts, The spec will also provide the integration databag and an example usage.


# Specification

The Gateway Route Configurator charm will act as a bridge between the Gateway API Integrator charm and the workload charm. It will use the new gateway-route relation to talk to the Gateway API Integrator charm and the old ingress integration to talk to the workload charm. The following sections describe the gateway-route relation, its databag, the Gateway Route Configurator charm’s config options, and an example of the resultant resources in Kubernetes (gateway, HTTPRoute, etc.).


# gateway-route integration

The gateway-route integration will let users serve their applications in the exact hostnames they prefer instead of under a path, which is the case for the ingress integration. The gateway-route integration will be a very light relation with only 6 fields. These fields are defined in the table below:

| ## Table 1: gateway-route integration fields |                                                     |                        |                                         |                   |
| -------------------------------------------- | --------------------------------------------------- | :--------------------: | --------------------------------------- | ----------------- |
| **Integration field**                        | **Description**                                     | **Is a config option** | **K8s Gateway API Field**               | **Default value** |
| paths                                        | Paths that will serve the workload application      |           `✅`          | `spec.rules.matches.path`               | `/`               |
| hostname                                     | The workload app will be served under this hostname |           `✅`          | `spec.hostnames`                        | `required`        |
| port                                         | Port that the workload app is served under          |           `❌`          | `spec.backendRefs.port`                 | Not applicable    |
| application                                  | The workload k8s application name                   |           `❌`          | Used when creating the service resource | Not applicable    |
| model-name                                   | The workload k8s applications model name            |           `❌`          | Used when creating the service resource | Not applicable    |

From these fields, the port, application, and model-name will be populated automatically through the ingress integration. The others will be charm configuration options in the Gateway Route Configurator charm.

In haproxy-route we allow multiple ports, but in here we only allow 1 port. Because in K8s charms it is recommended to expose 1 service per pod, thus you only need 1 port.


## Example usage and resultant K8s resources

Example configuration:

    paths: "/foo,/bar"
    hostname: "myapp.com"

Example integration data:

    {
    "paths": ["/foo", "/bar"],
    "hostname": "myapp.com",
    "port": 8080,
    "application": "my-service",
    "model": "juju-model"
    }

Resultant HTTPRoute:

    kind: HTTPRoute
    apiVersion: gateway.networking.k8s.io/v1
    metadata:
      name: my-app-route
      namespace: application-a
    spec:
      hostnames: ["myapp.com"]
      parentRefs:
      - name: my-gateway
        namespace: infra
      rules:
      - matches:
        - path:
            type: PathPrefix
            value: /foo
    - path:
            type: PathPrefix
            value: /bar
        backendRefs:      
          Group:   
          Kind:    Service
          Name:    gateway-api-integrator-my-service
          Port:    8080
          Weight:  1

Resultant service:

    Name:                     gateway-api-integrator-my-service
    Namespace:                model-name
    Labels:                   app.juju.is/created-by=gateway-api-integrator
                              app.kubernetes.io/managed-by=juju
                              gateway-api-integrator.charm.juju.is/managed-by=gateway-api-integrator
                              model.juju.is/id=9b112ac5-74a7-421f-8a54-c5e17df42337
                              model.juju.is/name=model-name
    Annotations:              <none>
    Selector:                 app.kubernetes.io/name=model-name
    Type:                     ClusterIP
    IP Family Policy:         SingleStack
    IP Families:              IPv4
    IP:                       10.152.183.159
    IPs:                      10.152.183.159
    Port:                     tcp-8000  8000/TCP
    TargetPort:               8000/TCP
    Endpoints:                10.1.0.88:8000,10.1.0.25:8000,10.1.0.40:8000
    Session Affinity:         None
    Internal Traffic Policy:  Cluster
    Events:                   <none>


# gateway-route Configurator Charm

This charm will work as a bridge between the workload and the Gateway API Integrator Charm. It will connect to the workload through `ingress` relation and connect to the Gateway API Integrator through` gateway-route` relation. It will combine the configuration options listed in **Table 1** and the information from the `ingress` relation to create a whole story for the `gateway-route` integration and provide it to the Gateway API Integrator charm. 

It will live in the same model as the workload charm and the Gateway API Integrator charm. It will **not support** cross-model integrations; the reasoning is explained in **the Further Information** section.

\
\



## Validations

### Hostname validation

For validation we will use the HAproxy charm's hostname validation method. For now we will copy-paste the related logic but will talk to Charm tech to see if we can put it into ops or if it's better to create a charmlib.

Inputs are validated against standard [Kubernetes hostname requirements](https://gateway-api.sigs.k8s.io/reference/spec/#hostname). Kubernetes requirements are a subset of RFC 1123. To be considered valid, a hostname must be a "precise" domain (e.g., `foo.example.com`)

**Constraints:**

- **Syntax:** Lowercase alphanumeric characters and hyphens only. No punctuation aside from the dot separator.

- **Boundary:** Labels must not start or end with a hyphen.

- **Restriction:** IP addresses are strictly prohibited.

- **Wildcard Scope:** Do not support any wildcards.

- **Length**: **min** 1, **max** 253.

**Regex Pattern:**

    ^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$


# **Further Information**

### Cross-Model Relations (CMR)

Cross-model relations are **not supported** in this iteration of the gateway-route integration.

**Rationale:**

- **Kubernetes Constraints:** The Kubernetes Service resource relies on label selectors to identify target Pods. Label selectors are namespace-scoped and cannot target Pods in a different namespace (model). Therefore, the Service resource must be created in the same model as the workload charm.

- **Architectural Pattern:** While HTTPRoute resources allow cross-namespace references, the requirement to place the Service in the workload namespace would necessitate deploying the Configurator charm into the workload model. This is an anti-pattern; the Configurator charm is designed for configuration logic, not for managing resources or running workloads.

- **Network Architecture:** Future iterations will rely exclusively on internal IPs rather than public IPs. Consequently, IPv4 scarcity is not a driver for supporting CMR in this context.


### Hostnames and additional-hostnames

The Kubernetes HTTPRoute resource already uses `hostnames` instead of `hostname` and `additional-hostname` but since most users will use only 1 hostname it is a UX decision to separate `hostnames` into `hostname` and `additional-hostnames`. And to keep this spec as simple as possible, the `additional-hostnames` field is removed. In the future, if the need arises, this field can be easily added.


# Spec History and Changelog

Please be thorough when recording changes and progress with the spec itself and the work resulting from it. Record every meeting, attendees and conclusions from the meeting.

|             |                 |                                                                       |                                                                          |
| ----------- | --------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **Date**    | **Status**      | **Author(s)**                                                         | **Comment**                                                              |
|  2025-11-20 |  Drafting       |  [Ali Ugur](mailto:ali.ugur@canonical.com)                            | Finished first draft.                                                    |
|  2025-11-21 |  Pending Review |  [Ali Ugur](mailto:ali.ugur@canonical.com)                            | Updated based on comments.                                               |
|  2025-11-21 |  Approved       |  [Trung Thanh Phan](mailto:trung.thanh.phan@canonical.com)            | LGTM after the comments during the review session are addressed, thanks! |
|  2025-11-21 |  Pending Review |  [Sebastien Georget](mailto:sebastien.georget@canonical.com)          | Can you please review? Thanks!                                           |
|  2025-11-21 |  Pending Review |  [Javier de la Puente Alonso](mailto:javier.delapuente@canonical.com) | Can you please review? Thanks!                                           |
|  2025-11-21 |  Pending Review |  [Arturo Seijas Fernandez](mailto:arturo.seijas@canonical.com)        | Can you please review? Thanks!                                           |
