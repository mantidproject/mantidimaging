Savu and hebi integration overview
==================================

Savu_ is a package developed at Diamond for processing tomographic data which is
integrated into mantidimaging via Hebi_, a RESTful API. The aim of the integration
is to be able to process data with savu's processing plugins via the gui, with a
similar UX to using the tomopy filters built in to the 'filters' window. Savu is
designed to run in a variety of environments, which makes the integration somewhat
complicated.

Savu workflow
-------------

Savu works by applying the plugins specified in a process list to the data in a folder.

A process list:
 - Is a nexus (.nxs) file
 - Starts with a loader plugin
 - Has one or more processing plugins
 - Optionally ends with a saver plugin
 - Internally to savu, can be built with `savu_config`

Hebi
----

Hebi_ is a REST api on top of savu which creates and monitors 'jobs' running in savu.
It is WIP, and the API can be expected to evolve over time.

Imaging to hebi to savu and back
--------------------------------

How everything is connected:
 - |container_setup|
 - An http client is connected to hebi to submit jobs, ask for plugin details etc.
 - A websocket client waits for messages from hebi, signalling when jobs complete.

To apply a 'savu filter' to an image stack:
 - |process_list_built|
 - Submits a job to hebi with the pl and path to the input data.
 - Hebi validates everything and starts savu as a subprocess.
 - Once savu completes, hebi sends a message to imaging's ws client.
 - Imaging then loads an image stack from the folder savu wrote it's output to.

.. |container_setup| replace:: A hebi container, which extends a savu container, runs locally. It is either started as a separate process, or automatically_ when the GUI starts up, as a subprocess.
.. |process_list_built| replace:: Imaging creates and saves a process list. It is composed of a (fixed) loader, a single processor with parameters taken from the GUI, and a (fixed) saver.
.. _Hebi: https://github.com/DiamondLightSource/hebi
.. _Savu: https://github.com/DiamondLightSource/savu
.. _automatically: https://github.com/mantidproject/mantidimaging/pull/355
