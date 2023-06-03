Installation
============

The recommended installation approach is using the built-in Helm chart, with Kubernetes.

Installation with Kubernetes
----------------------------

To install the Helm chart for µchan, please ensure you have the following prerequisites
in place:

1. Set up a Kubernetes cluster: If you don't have a Kubernetes cluster already,
   provision one using a tool like Minikube for local development or choose a cloud
   provider such as Google Kubernetes Engine (GKE), Amazon Elastic Kubernetes Service
   (EKS), or Microsoft Azure Kubernetes Service (AKS) to create a cluster.
2. Configure kubectl: Install the :code:`kubectl` command-line tool and configure it to
   connect to your Kubernetes cluster. You'll need to set up the cluster context and
   ensure you have the necessary credentials to access the cluster. You can find
   detailed instructions on how to configure :code:`kubectl` in the Kubernetes
   documentation specific to your cluster provider.
3. Install Helm: Ensure that you have Helm installed on your system. Helm is a package
   manager for Kubernetes that simplifies the deployment and management of applications.
   Refer to the `Helm documentation <https://helm.sh/docs/intro/install/)>`_ for
   installation instructions tailored to your operating system.

Once you have completed these steps, you will have a functioning Kubernetes cluster with
`kubectl` and Helm installed, ready to proceed with the installation of the Helm chart
for µchan.

Install varnish-operator
~~~~~~~~~~~~~~~~~~~~~~~~

µchan leverages extensive caching techniques to optimize the rapid delivery of web
pages. One crucial component in this architecture is Varnish, which functions as a
document cache, capable of caching complete HTML responses.

When integrating Varnish into the Kubernetes ingress-service-pod model, the recommended
approach is to employ the `varnish-operator <https://ibm.github.io/varnish-operator/>`_.
This operator efficiently manages the reloading of the VCL configuration in response to
changes in the Pod topology.

Configure the Helm chart and install varnish-operator:

.. code-block:: text

    $ helm repo add varnish-operator https://raw.githubusercontent.com/IBM/varnish-operator/main/helm-releases
    $ helm repo update
    $ helm install varnish-operator --namespace varnish-operator varnish-operator/varnish-operator

While running µchan without Varnish is possible, it's important to note that it may
negatively impact performance. By default, µchan is designed to work seamlessly with
Varnish for optimal results. However, if you wish to disable the Varnish integration,
you can achieve this by disabling it in your :code:`values.yaml`:

.. code-block:: yaml

    varnish:
        enabled: false

Keep in mind that this configuration change may result in decreased
performance and may not provide the same level of caching and page delivery speed as
when Varnish is enabled.


Prepare values.yaml
~~~~~~~~~~~~~~~~~~~

To ensure proper configuration of the Helm chart, please follow these steps:

1. Create a file called `values.yaml`.

2. Copy and paste the following contents into the `values.yaml` file:

.. code-block:: yaml

    uchan:
      siteUrl: "https://<your_domain_here>"
      assetUrl: "https://<your_domain_here>/static/"

    ingress:
      enabled: true
      hosts:
        - host: <your_domain_here>
          paths:
            - path: /
              pathType: ImplementationSpecific

3. Replace `<your_domain_here>` with your actual domain name for the following values:

   - `uchan.siteUrl`: Replace with the URL where your site will be accessible.
   - `uchan.assetUrl`: Replace with the URL where your images  will be hosted. By
     default, µchan delives the assets.
   - `ingress.hosts[0].host`: Replace with the your domain (without the schema).


Get the µchan Helm chart
~~~~~~~~~~~~~~~~~~~~~~~~

The helm chart is embedded in the repository. Clone the repository:

.. code-block:: text

    $ git clone https://github.com/floens/uchan
    $ cd uchan

Install the Helm chart. Change the namespace as you seem fit:

.. code-block:: text

    $ helm install uchan charts/uchan/ -n uchan -f values.yaml

µchan is now installed. Try to access the mod portal as indicated by the installation
notes.
