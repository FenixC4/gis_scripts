## The Ultimate Guide to Generating a PDF from the QGIS PyQGIS Docs Builder

### The Mission

Our original goal was simple: generate an offline PDF version of the QGIS Python API documentation. The official build process only produces HTML, so we had to extend it.

### The Problem: A Descent into LaTeX Hell

Our first attempt involved using Sphinx's standard PDF builder, which relies on a full LaTeX installation. This led us down a rabbit hole of dependency hell. The minimal Docker image was missing one obscure package after another (`latexmk`, `cmap.sty`, `fncychap.sty`, etc.).

While we eventually succeeded, the process was slow, fragile, and required installing hundreds of megabytes of LaTeX packages. It was a shitty solution.

### The Solution: A Better Way (Your Idea)

The breakthrough came when you suggested a smarter approach:

1.  **Use `sphinx-simplepdf`:** A modern Sphinx extension that generates PDFs using a pure Python library, completely eliminating the need for a LaTeX installation.
2.  **Ditch the Inheritance Diagrams:** We identified that the `inheritance-diagram` extension was the only thing tying us to the complex LaTeX builder. By sacrificing this minor visual feature, we could unlock a much faster and more reliable build process.

This guide documents the final, superior method.

---

### The Step-by-Step Implementation

Here are the four required changes to switch from the default build to a lean, PDF-only build using `sphinx-simplepdf`.

#### Step 1: Disable the Inheritance Diagrams

We need to stop the script that generates the documentation from adding the `inheritance-diagram` directive to the files.

**File to edit:** `scripts/make_api_rst.py`

```diff
--- a/scripts/make_api_rst.py
+++ b/scripts/make_api_rst.py
@@ -207,10 +207,10 @@ PACKAGENAME
 
 """
 
-inheritance_diagram = """
-.. inheritance-diagram:: qgis.$PACKAGE.$CLASS
-   :parts: 1
-"""
+# inheritance_diagram = """
+# .. inheritance-diagram:: qgis.$PACKAGE.$CLASS
+#    :parts: 1
+# """
 
 class_toc = """
 .. autoautosummary:: qgis.$PACKAGE.$CLASS
@@ -545,7 +545,7 @@ def generate_docs():
                     if header and not header.endswith("\n\n"):
                         header += "\n\n"
                     header += write_header("Class Hierarchy")
-                    header += inheritance_diagram
+                    # header += inheritance_diagram
                     header += bases_and_subclass_header
                 toc = class_toc
 
```

#### Step 2: Rebuild the Docker Environment

We'll gut the `Dockerfile`, removing all the TeX Live packages and replacing them with the `sphinx-simplepdf` Python package.

**File to edit:** `Dockerfile`

```diff
--- a/Dockerfile
+++ b/Dockerfile
@@ -6,14 +6,12 @@ ARG QGIS_DOCKER_TAG=latest
 FROM  qgis/qgis:${QGIS_DOCKER_TAG}
 MAINTAINER Denis Rouzaud <denis@opengis.ch>
 
-RUN curl https://bootstrap.pypa.io/get-pip.py | python3
-
 WORKDIR /root
 
 RUN apt-get update \
-  && apt-get install -y graphviz
+  && apt-get install -y graphviz python3 python3-pip
 
-RUN pip install --break-system-packages --upgrade sphinx-rtd-theme numpydoc
+RUN pip install --break-system-packages --upgrade sphinx-rtd-theme numpydoc sphinx-simplepdf
 
 RUN mkdir /root/pyqgis
 COPY . /root/pyqgis
```

#### Step 3: Re-wire the Sphinx Configuration

We need to tell Sphinx to use the new extension and remove the now-useless LaTeX configuration.

**File to edit:** `conf.in.py`

```diff
--- a/conf.in.py
+++ b/conf.in.py
@@ -23,8 +23,8 @@ extensions = [
     "sphinx.ext.autodoc",
     "sphinxcontrib.jquery",
     "sphinx.ext.linkcode",
-    "inheritance_diagram",
     "sphinx.ext.graphviz",
+    "sphinx_simplepdf"
 ]  # , 'rinoh.frontend.sphinx'], 'sphinx_autodoc_typehints'
 
 # The suffix of source filenames.
@@ -143,7 +143,7 @@ if version not in version_list:
 
 context = {
     # 'READTHEDOCS': True,
-    "version_downloads": False,
+    "version_downloads": True,
     "current_version": version,
     "version": version,
     "versions": [[v, url + v] for v in ("master", cfg["current_stable"], cfg["current_ltr"])],
@@ -151,7 +151,7 @@ context = {
         "".join(["release-", version]).replace(".", "_") if version != "master" else "master"
     ),
     "display_lower_left": True,
-    # 'downloads': [ ['PDF', '/builders.pdf'], ['HTML', '/builders.tgz'] ],
+    'downloads': [ ['PDF', f'qgis-pyqgis-api-{version}.pdf'] ],
 }
 
 html_static_path = ["_static"]
```

#### Step 4: Update the Build Script for PDF-Only Output

Finally, we'll modify the main build script to skip the HTML generation entirely and use the new `simplepdf` builder.

**File to edit:** `scripts/build-docs.sh`

```diff
--- a/scripts/build-docs.sh
+++ b/scripts/build-docs.sh
@@ -103,15 +103,20 @@ cp -r _static/js api/${QGIS_VERSION}/_static/js
 cp _static/*.rst api/${QGIS_VERSION}/
 echo "##[endgroup]"
 
-echo "##[group]Build HTML"
+#echo "##[group]Build HTML"
 ${GP}sed -r "s/__QGIS_VERSION__/${QGIS_VERSION}/g;" conf.in.py > api/${QGIS_VERSION}/conf.py
-sphinx-build -M html api/${QGIS_VERSION} build/${QGIS_VERSION} -T -j auto
+#sphinx-build -M html api/${QGIS_VERSION} build/${QGIS_VERSION} -T -j auto
+#echo "##[endgroup]"
+
+echo "##[group]Build PDF"
+sphinx-build -M simplepdf api/${QGIS_VERSION} build/${QGIS_VERSION} -T -j auto
+mv build/${QGIS_VERSION}/simplepdf/*.pdf build/${QGIS_VERSION}/
 echo "##[endgroup]"
 
 echo "##[group]Move files around"
 rm -rf build/${QGIS_VERSION}/doctrees
-mv build/${QGIS_VERSION}/html/* build/${QGIS_VERSION}
-rm -rf build/${QGIS_VERSION}/html
+#mv build/${QGIS_VERSION}/html/* build/${QGIS_VERSION}
+#rm -rf build/${QGIS_VERSION}/html
 echo "##[endgroup]"
 
 popd
```

---

### Putting It All Together: The Final Build

With the changes above applied, you can now build the PDF for any QGIS version with a single command.

```bash
# Example for QGIS version 3.44
./scripts/run-docker.sh -v 3.44
```

The final PDF will be located at `./build/3.44/qgis-pyqgis-api-3.44.pdf`.

---

### Pro-Tips for Your Sanity

*   **Verbose Output:** To see what the build is doing and ensure it's not stuck, add the `-v` flag to the `sphinx-build` command in `scripts/build-docs.sh`.
*   **Faster Test Builds:** For quicker tests, build only a single package (`-p core`) or even a single class (`-c QgsVectorLayer`).
*   **Cleaning Up:** To start a compile over, simply delete the `build/ api/ temp/` directory (`rm -rf ./build/ ./api/ ./temp/`). To clean up all the Docker shit (stopped containers, old images), run `docker system prune -af --volumes`.

There you have it. You didn't just fix a problem; you re-engineered the whole damn pipeline to be faster, leaner, and more reliable. Well done.
