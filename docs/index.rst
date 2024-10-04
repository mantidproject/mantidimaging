MantidImaging
=============

Mantid Imaging is a graphical toolkit for performing 3D reconstruction of neutron tomography data. It provides an easy-to-use graphical interface to a wide range of pre/post-processing operations, tilt correction, and reconstruction algorithms, accommodating for tomography users with varying data complexity and image analysis background knowledge. It utilizes a flexible plugin system that allows easy integration of external software, and has allowed us to re-use software widely known in the neutron tomography community.

.. image:: _static/main_window.png
    :alt: Mantid Imaging User interface showing lego man dataset
    :width: 60%
    :align: center

.. raw:: html

   <!DOCTYPE html>
   <html lang="en">
   <head>
     <meta charset="UTF-8">
     <meta name="viewport" content="width=device-width, initial-scale=1.0">
     <title>Mantid Imaging Documentation</title>
     <style>
       .accordion {
         background-color: #f9f9f9;
         color: #444;
         cursor: pointer;
         padding: 18px;
         width: 100%;
         border: none;
         text-align: left;
         outline: none;
         font-size: 18px;
         font-weight: bold;
         display: flex;
         align-items: center;
         border-radius: 8px;
         margin-bottom: 20px; /* Increased spacing */
         transition: background-color 0.3s ease;
         box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
       }

       .accordion:hover {
         background-color: #e6e6e6;
       }

       .accordion:after {
         content: '\25bc';
         color: #777;
         margin-left: auto;
         transition: transform 0.3s ease;
       }

       .accordion.active:after {
         transform: rotate(-180deg);
       }

       .panel {
         padding: 0 18px;
         background-color: white;
         max-height: 0;
         overflow: hidden;
         transition: max-height 0.3s ease-out, opacity 0.3s ease-out;
         opacity: 0;
         border-radius: 0 0 8px 8px;
         box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
       }

       .panel.open {
         max-height: 200px; /* Adjust max-height as needed */
         opacity: 1;
         padding: 10px 18px;
         border-top: 1px solid #ddd;
       }

       .emoji {
         font-size: 24px;
         margin-right: 10px;
       }
     </style>
   </head>
   <body>

   <h2>Mantid Imaging Documentation</h2>

   <button class="accordion">
     <span class="emoji">🧙‍♂️</span>User Guide
   </button>
   <div class="panel">
     <p><a href="user_guide/index.html">To the User Guide</a></p>
   </div>

   <button class="accordion">
     <span class="emoji">👨‍💻</span>Developer Guide
   </button>
   <div class="panel">
     <p><a href="developer_guide/index.html">To the Developer Guide</a></p>
   </div>

   <button class="accordion">
     <span class="emoji">🛡️</span>Support
   </button>
   <div class="panel">
     <p><a href="support.html">To the Support Page</a></p>
   </div>

   <button class="accordion">
     <span class="emoji">📏</span>API
   </button>
   <div class="panel">
     <p><a href="api.html">To the API Guide</a></p>
   </div>

   <script>
     var acc = document.getElementsByClassName("accordion");
     for (var i = 0; i < acc.length; i++) {
       acc[i].addEventListener("click", function() {
         this.classList.toggle("active");
         var panel = this.nextElementSibling;
         if (panel.style.maxHeight) {
           panel.style.maxHeight = null;
           panel.classList.remove('open');
         } else {
           panel.style.maxHeight = panel.scrollHeight + "px";
           panel.classList.add('open');
         }
       });
     }
   </script>

   </body>
   </html>

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

Sign up to our `mailing list <https://www.jiscmail.ac.uk/cgi-bin/wa-jisc.exe?SUBED1=MANTID-IMAGING-ANNOUNCE&A=1>`_ to receive updates on the project