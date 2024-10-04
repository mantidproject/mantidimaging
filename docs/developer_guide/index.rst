.. _developer_guide:

Developer Guide
===============

Welcome to the developer guide. This guide is divided into several sections based on the purpose of the documentation.

.. raw:: html

   <style>
      a {
          color: #333; /* Black-grey for links */
          text-decoration: none;
      }

      a:hover {
          text-decoration: underline;
      }

      .doc-dropdown {
          width: 100%;
          text-align: left;
          margin-bottom: 20px;
          padding: 0;
          list-style-type: none;
      }

      /* Add margin to each dropdown menu item for spacing */
      .doc-dropdown li {
          margin-bottom: 15px; /* Space between dropdowns */
      }

      .doc-dropdown button {
          background-color: #f1f1f1; /* Light grey for the buttons */
          color: #333; /* Black-grey for the button text */
          cursor: pointer;
          padding: 12px;
          width: 100%;
          border: 1px solid #d3d3d3; /* Border color to match the grey theme */
          text-align: left;
          outline: none;
          font-size: 16px;
          font-weight: 600;
          display: flex;
          align-items: center;
          border-radius: 4px;
          transition: background-color 0.2s ease, padding-left 0.2s ease;
      }

      .doc-dropdown button:hover {
          background-color: #e0e0e0; /* Darker grey on hover */
          padding-left: 16px;
      }

      .doc-dropdown button:after {
          content: '\25bc';
          color: #333; /* Black-grey for the arrow */
          margin-left: auto;
          transition: transform 0.2s ease;
      }

      .doc-dropdown button.active:after {
          transform: rotate(-180deg);
      }

      .doc-dropdown .panel {
          padding: 0 18px;
          background-color: #f9f9f9;
          max-height: 0;
          overflow: hidden;
          transition: max-height 0.3s ease-out, opacity 0.3s ease-out;
          opacity: 0;
      }

      .doc-dropdown .panel.open {
          max-height: 250px;
          opacity: 1;
          padding: 10px 0;
      }

      .doc-button {
          display: block;
          padding: 8px 12px;
          font-size: 14px;
          background-color: #f1f1f1;
          color: #333; /* Black-grey for the links inside the panels */
          text-decoration: none;
          border-left: 3px solid transparent;
          transition: background-color 0.2s ease, border-left-color 0.2s ease;
      }

      .doc-button:hover {
          background-color: #e0e0e0;
          border-left-color: #333; /* Dark grey border on hover */
      }

      h1, h2, h3, h4, h5, h6 {
          color: #333; /* Black-grey for headings */
      }

      p, li {
          color: #333; /* Black-grey for paragraphs and list items */
      }

   </style>

   <ul class="doc-dropdown">
     <li>
       <button class="accordion">🚀 Tutorials</button>
       <div class="panel">
         <a href="tutorials/index.html" class="doc-button">Getting Started</a>
       </div>
     </li>

     <li>
       <button class="accordion">🔧 How-To Guides</button>
       <div class="panel">
         <a href="how-to-guides/developer_guide.html" class="doc-button">Developer Guide</a>
         <a href="how-to-guides/debugging.html" class="doc-button">Debugging</a>
         <a href="how-to-guides/testing.html" class="doc-button">Testing</a>
       </div>
     </li>

     <li>
       <button class="accordion">💡 Explanations</button>
       <div class="panel">
         <a href="explanations/documentation.html" class="doc-button">Documentation</a>
         <a href="explanations/developer_conventions.html" class="doc-button">Developer Conventions</a>
       </div>
     </li>

     <li>
       <button class="accordion">📚 Reference</button>
       <div class="panel">
         <a href="../support.html" class="doc-button">Support</a>
         <a href="../api.html" class="doc-button">API</a>
         <a href="../release_notes/next.html" class="doc-button">Release Notes (Next)</a>
       </div>
     </li>
   </ul>

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

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   tutorials/index
   how-to-guides/index
   explanations/index
   reference/index
