.. _developer_guide:

MantidImaging
=============

Mantid Imaging is a graphical toolkit for performing 3D reconstruction of neutron tomography data. It provides an easy-to-use graphical interface to a wide range of pre/post-processing operations, tilt correction, and reconstruction algorithms, accommodating for tomography users with varying data complexity and image analysis background knowledge. It utilizes a flexible plugin system that allows easy integration of external software, and has allowed us to re-use software widely known in the neutron tomography community.

.. image:: _static/main_window.png
    :alt: Mantid Imaging User interface showing lego man dataset
    :width: 60%
    :align: center

.. raw:: html

   <style>
      .doc-topic {
          width: 45%;
          display: inline-block;
          text-align: center;
          margin: 10px;
          border: 1px solid #ddd;
          padding: 10px;
          border-radius: 8px;
          background-color: #f9f9f9;
          vertical-align: top;
          height: 320px;
          overflow: hidden;
      }
      .doc-topic h2 {
          color: #1f77b4;
          font-size: 22px;
          font-weight: bold;
          text-decoration: none;
          margin-bottom: 5px;
      }
      .doc-topic span {
          font-size: 60px;
          display: block;
          margin-bottom: 5px;
      }
      .doc-topic p {
          margin-bottom: 5px;
          font-size: 16px;
      }
      .doc-button {
          display: inline-block;
          padding: 8px 12px;
          font-size: 16px;
          background-color: #333;
          color: white;
          text-decoration: none;
          border-radius: 5px;
          margin-top: 5px;
          width: 160px;
          height: auto;
          text-align: center;
          line-height: 1.2;
          box-sizing: border-box;
      }
      .doc-button:hover {
          text-decoration: underline;
      }
   </style>

   <div class="doc-topic">
      <span>🧙‍♂️</span>
      <h2><a href="#user-guide">User Guide</a></h2>
      <p>Documentation for using Mantid Imaging.</p>
      <a href="user_guide/index.html" class="doc-button">To the User Guide</a>
   </div>

   <div class="doc-topic">
      <span>👨‍💻</span>
      <h2><a href="#developer-guide">Developer Guide</a></h2>
      <p>Guidance for contributing to Mantid Imaging development.</p>
      <a href="developer_guide/index.html" class="doc-button">To the Developer Guide</a>
   </div>

   <div class="doc-topic">
      <span>🛡️</span>
      <h2><a href="#support">Support</a></h2>
      <p>Get help and support for using Mantid Imaging.</p>
      <a href="support.html" class="doc-button">To the Support Page</a>
   </div>

   <div class="doc-topic">
      <span>📏</span>
      <h2><a href="#api">API</a></h2>
      <p>API reference for Mantid Imaging functionality.</p>
      <a href="api.html" class="doc-button">To the API Guide</a>
   </div>

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   overview
   installation
   user_guide/index
   developer_guide/index
   support
   troubleshooting
   api
   release_notes/index

.. toctree::
   :caption: Links:

   Code Repository <https://github.com/mantidproject/mantidimaging>
   Anaconda Package <https://anaconda.org/mantidimaging/mantidimaging>

Please cite as:
Akello-Egwel, Dolica; Allen, Jack; Baust, Rachel; Gigg, Martyn; Jones, Samuel; Meigh, Ashley; Nixon, Daniel; Stock, Samuel; Sullivan, Michael; Tasev, Dimitar; Taylor, Will; Tygier, Sam. (2024). Mantid Imaging (2.8.0), Zenodo https://doi.org/10.5281/zenodo.4728059

(See `Zenodo <https://doi.org/10.5281/zenodo.4728059>`_ for citing specific versions).
