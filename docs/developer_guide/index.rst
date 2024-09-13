.. _developer_guide:

Developer Guide
===============

Welcome to the developer guide. This guide is divided into several sections based on the purpose of the documentation.

.. raw:: html

   <style>
      .doc-topic {
          width: 45%;
          display: inline-block;
          text-align: center;
          margin: 10px;
          border: 1px solid #ddd;
          padding: 20px;
          border-radius: 8px;
          background-color: #f9f9f9;
      }
      .doc-topic h2 {
          color: #1f77b4;
      }
      .doc-topic img {
          width: 40px;
          height: 40px;
      }
      .doc-button {
          display: inline-block;
          padding: 10px 15px;
          font-size: 14px;
          background-color: #333;
          color: white;
          text-decoration: none;
          border-radius: 5px;
          margin-top: 10px;
      }
   </style>

   <div class="doc-topic">
      <img src="_static/getting_started.png" alt="Getting Started">
      <h2><a href="#tutorials">Getting Started</a></h2>
      <p>Set up your environment and get started with development.</p>
      <a href="started.html" class="doc-button">To the Getting Started Guide</a>
   </div>

   <div class="doc-topic">
      <img src="_static/how_to.png" alt="How To Guides">
      <h2><a href="#how-to-guides">How-To Guides</a></h2>
      <p>Step-by-step instructions for specific development tasks.</p>
      <a href="command.html" class="doc-button">To the How-To Guides</a>
   </div>

   <div class="doc-topic">
      <img src="_static/explanations.png" alt="Explanations">
      <h2><a href="#explanations">Explanations</a></h2>
      <p>Conceptual explanations of the project's architecture and developer guidelines.</p>
      <a href="documentation.html" class="doc-button">To the Explanations</a>
   </div>

   <div class="doc-topic">
      <img src="_static/reference.png" alt="Reference">
      <h2><a href="#reference">Reference</a></h2>
      <p>API reference and internal tools documentation.</p>
      <a href="support.html" class="doc-button">To the Reference Guide</a>
   </div>

.. _tutorials:

Tutorials
=========

.. toctree::
   :maxdepth: 2

   started.rst

.. _explanations:

Explanations
============

.. toctree::
   :maxdepth: 2

   documentation.rst
   developer_conventions.rst
   release.rst

.. _how-to-guides:

How-To Guides
=============

.. toctree::
   :maxdepth: 2

   command.rst
   debugging.rst
   conda_packaging_and_docker_image.rst
   testing.rst

.. _reference:

Reference
=========

.. toctree::
   :maxdepth: 2

   ../support.rst
   ../api.rst
   ../release_notes/next.rst
