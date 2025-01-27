Developer Conventions
=====================

Dependencies
------------

Mantid Imaging makes use of a number of python modules. To ensure that these get installed for users they can be listed as dependencies.

Dependencies are categorised by when they are needed:

* Runtime: Needed to run Mantid Imaging.
* Development: Only needed during development.

and how they are installed:

* Conda: suitable version available in the conda repository. Preferred.
* Pip: suitable version available in the PyPI repository.

Conda runtime dependencies can be specified in `conda/meta.yaml`. These will be tracked automatically by conda and installed when ever the mantidimaging package installed.

Pip runtime dependencies can't be tracked automatically and so must be installed as part of the environment. These should be listed in `environment.yml`. Due to technical limitations they must also be duplicated in the pip section of `environment-dev.yml`.

Development dependencies should be listed in `environment-dev.yml`, with conda and pip dependencies placed in the correct place.

When updating dependencies or modifying `conda/meta.yaml`, it is important to test that there are no conflicts that will prevent the package being built. This can be done by running

.. code::

    make build-conda-package


Version Control
---------------

Mantid Imaging uses git for version control. The repository is hosted on GitHub at `Mantid Imaging <https://github.com/mantidproject/mantidimaging>`_.

Before you start contributing to Mantid Imaging, please ensure you have a GitHub account with `2FA <https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication>`_ enabled and have configured signed commits with a `GPG key <https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits>`_. This is important to ensure that the codebase remains secure and that contributions can be attributed correctly.


Issues
~~~~~~

As a general rule of thumb, for every issue you complete, you should try to also review someone elses pull request. This helps maintain code frequency, and prevents any one person from becoming a bottleneck due to issues not being reviewed.

When you find a bug or have an idea for a new feature, please create an issue on the `Mantid Imaging GitHub repository <https://github.com/mantidproject/mantidimaging>`_ after first checking that the issue does not already exist and that you have agreed with the Mantid Imaging team that the issue is valid.

When creating an issue, please provide as much information as possible, including:

* Steps to reproduce the issue if it is a bug.
* A clear description of the feature you would like to see if it is a feature request. - remember to include the use case and argue to importance of the feature.
* Any relevant screenshots or logs.
* Any other information that you think may be useful.

When creating an issue, please ensure that you assign the issue to yourself if you are going to work on it or leave the assignment blank if not. This will prevent multiple people from working on the same issue at the same time.

Please also ensure that any relevant labels are added to the issue. This will help the Mantid Imaging team to prioritise the issue and ensure that it is worked on in a timely manner.

Once you have completed the above, you will also need to point the ticket with a number which will act as a rough estimate for the time it will take to complete the issue in whole days (round up to the nearest day), including any necessary research someone may need to do and the time to review and test.

Please assign the newly created issue to the `Mantid Imaging work project board <https://github.com/orgs/mantidproject/projects/13>`_, and set the status to "Todo", We kindly ask that you do not point or associate the issue to a sprint. This will make the issue easier for the Mantid Imaging team to find and place into an appropriate sprint.
During sprint planning the Mantid Imaging team will assign issues to be worked on in the next sprint to the sprint project board - `current sprint <https://github.com/orgs/mantidproject/projects/13/views/6>`_.  



If you are unsure about any of the above, please ask a member of the Mantid Imaging team for help.

Branches
~~~~~~~~

Mantid Imaging treats the ``main`` branch as the default branch. This branch should always be in a working state and should be used as the base for all new features and bug fixes.

When working on a new feature or bug fix, you should create a new development branch from the ``main`` branch after you have first checked that your local ``main`` branch is up to date with the remote ``main`` branch. This can be checked by running to following command:

.. code::

    git fetch origin main && git pull origin main


* ``git fetch origin main`` will fetch the latest changes from the remote ``main`` branch of the origin repository, updating your local copy of the remote-tracking branch ``origin/main`` with the latest commits from the remote repository.

* ``git pull origin main`` will then pull the latest changes from the remote ``main`` branch of the origin repository into your local ``main`` branch. 

In summary, this command updates your local branch with the latest changes from the remote ``main`` branch. **You do not need to checkout the main branch to do this**.

The branch should be named in the following format:

.. code::

    <issue_number>_short_description    # e.g. 1234_add_new_feature


You can create a new branch by running the following command (replacing ``<issue_number>_short_description`` with the relevant information):

.. code::

    git switch -c <issue_number>_short_description


The short description is commonly similar if not the same as the issue title. The description should be in lowercase and use underscores instead of spaces.

Commit Format
~~~~~~~~~~~~~

Commits act as a historical record of changes made to the codebase. They have the power to add context and clarity to the codebase, but only if they are written well.

The best commits are those with a clear title and detailed description explaining the changes made. The title should be in the imperative mood (i.e. written as a command or instruction) and should be no longer than 50 characters. The description should be no longer than 72 characters per line and should be wrapped at 72 characters.

Though commits can be made using only a summary, it is recommended to also write a description, even if you think it is unnecessary because from a reviewers perspective, it is always better to have more information than less.

The order of commits can be just as important as the commits themselves. Commits should be ordered in a logical manner and help tell the reviewer or another developer in the future the story of changes made, which may be slightly different from the order you made them in.

A good reference for writing commits is the GitHub blog post `"Write Better Commits, Build Better Projects" <https://github.blog/developer-skills/github/write-better-commits-build-better-projects/>`_ which will walk you through both how to write better commits, but also how to easily re-order commits using `interactive rebase <https://docs.github.com/en/get-started/using-git/about-git-rebase>`_.

Now is a good time to mention that it's important not to make commits too big. Not only are small, concise commits easier to review and understand, they also make it easier to revert if necessary.

Pull Requests
~~~~~~~~~~~~~

When you have completed your work on a new feature or bug fix, We ask that you check your work thoroughly to make sure it works functionally as you expect it too and that tests pass on your machine locally. Once you are happy with your branch, you should create a pull request (PR). There are two types of PR, a draft PR and a regular PR.

A draft PR can be useful if you wish to start a conversation with collaborators as soon as your work has reached a point where you would like feedback. It's important to note that once you make a draft PR, all changes pushed to the remote development branch will trigger Mantid Imagings `GitHub workflows <https://github.com/mantidproject/mantidimaging/actions>`_, which will run static analysis checks, run all unit tests, screenshot tests, and finally build the documentation. This can be useful to see if your changes have broken anything, though running them is time consuming.
Only make a draft PR when you are as close as possible to finishing your work if you haven't already. This will save on compute time by not triggering the workflows on every push. This will also help avoid any confusion as to whether the PR is ready for review or not - though if your PR is a draft, it should be assumed that it is not yet ready for review.

Once you are happy with your work, it passes tests and you are ready for it to be reviewed, you should convert the draft PR to a regular PR (skipping the draft PR stage is also fine). Make sure to assign yourself to the PR if you haven't already under "Assignees" (not as the reviewer). Then move your issue to the "Review" column on the `project board <https://github.com/orgs/mantidproject/projects/13/views/6?>`_ your issue is associated with, which will let the Mantid Imaging team know that your PR is ready for review.

When writing a PR, it is important to provide a clear title and description following the provided `template <https://github.com/mantidproject/mantidimaging/blob/main/.github/pull_request_template.md>`_. The Template will ask you to reference the associated issue related to the proposed changes and to clearly describe exactly what you have done in the PR, be careful no to repeat the issue description.
It is important that the description is written assuming no prior knowledge of the issue or work done and there is no assumed context. This will improve the accessibility of the PR, ensuring anyone within the Mantid Imaging team can review your proposed changes with a confident understanding of your approach to solving the issue.
Additionally, it is important to describe how you tested your work and what you did to ensure that your changes work as expected. This could include describing that you created additional unit tests and/or that you manually tested the changes and how you tested them. This will help the reviewer understand the scope of your testing and how confident you are that your changes work as expected.
To improve accessibility to your PR further, it is also important that you provide step by step instruction on how to test your PR including any necessary setup to follow your instructions - note that the reviewer can and should also try to test your PR in a different way to ensure that the changes work as expected in addition to following your instructions.

Labelling your PR can provide a little more context by describing the category of the PR such as whether or not is is solving a bug, or if the PR is a release essential which may help the Mantid Imaging team to prioritize your PR. 

**PLEASE NOTE**: the "rebuild_docker 🐋" label should only be added to your PR if you wish force rebuild the docker containers for your branch. Once added, the docker containers will be rebuilt. To do this again, simply remove the label and add it back again.

If your PR changes only change a tiny part of the codebase and may not even have an associated issue, this could be considered as a flash PR. Please add "Flash PR" to the start of the PR title if this is the case and add to the project "`Mantid Imaging Work <https://github.com/orgs/mantidproject/projects/13/views/6>`_", making sure to also add to the correct column on the project board which will likely be "review".

Reviewing a Pull Request
~~~~~~~~~~~~~~~~~~~~~~~~~

When reviewing a pull request (PR), it is important to provide constructive feedback. Feedback should be clear, concise and actionable. It is important to remember that the goal of a review is to improve the codebase, and not to criticise the author. It is also important to understand that the author may not have the same context as you and may have made a mistake or oversight that you have not. It is important to be patient and understanding when reviewing a PR as the author may have a different perspective on the issue than you do or different experience level.

When reviewing a PR, it is important to check the following:

1. **Linked Issue**: The PR is linked to the correct issue. If the PR is a flash PR, then no linked issue is needed. If the PR if a flash PR, check that is has been added to the correct project board and column.

2. **Description**: The PR description is clear and concise, and the author has provided step by step instructions on how to test the PR. If the PR description is not clear, it is important to ask the author to clarify. If the author has not provided step by step instructions on how to test the PR, it is important to ask the author to provide them.

3. **Code Quality**: The code is well written and follows the style of other code in the Mantid Imaging codebase.

4. **Testing**: The code is well tested and that the tests pass. If new code has been added, it is important to check that the tests cover the new code and that the tests are well written. Please note that this may not always be possible. As a reviewer, it is your job to work with the PR author to maintin good coverage of the codebase and prevent coverage from dropping when new code is merged in.

5. **Documentation**: The code is well documented and that the documentation is clear and concise. If the code is not well documented, it is important to ask the author to add documentation if you feel that it is necessary. If you don't understand the code, that in itself is a good argument for the code to be documented. If you are unsure about the documentation, please ask the author to clarify. Jumping on a video call can also be useful to ask the author to provide you with a code walk through to help you understand the code.

6. **Optimization**: The code is optimized, but not over optimized. It is important to ensure that the code is optimized for performance, but not at the expense of readability or maintainability. If you feel that the code is over optimized, it is important to ask the author to simplify the code.

7. **Commits**: Commits are well written and seem to be in a logical order. If the commits are not in a logical order, it is important to ask the author to re-order the commits. If the commits are not well written, it is important to ask the author to re-write the commits to help tell the story of the changes made as this will save future developers time when trying to understand the changes made.

8. **Release Notes**: If applicable, the PR author has added release notes and linked the path location in the PR. If the PR author has not added release notes, it is important to ask the author to add them if needed.

9. **GUI Changes**: If the PR makes changes to the GUI, which affects the test results from applitools, it is important for  the author of the POR to uncomment and follow the instruction in the PR template under the "Documentation and Additional Notes" section. Additionally, it is equally important that the reviewer checks that the author has followed the instructions correctly and actions the necessary steps required of the reviewer post-merge.

When reviewing a PR, there are many things to consider and in turn miss which could lead to bugs being merged into the codebase. While bugs will indefinitely make there way into the production code, minimizing this is important. To help prevent you from missing things as part of your review and to make checking all the above more manageable, we recommend going through the code a number of times as part of your review, checking only one or two of the above points each time. 


Pull Requests which Include GUI Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a PR includes changes to the GUI which either cause existing `Applitools <https://applitools.com/?utm_term=applitools&utm_source=google&utm_medium=paid-search&utm_content=free-account&utm_campaign=brand-primary&gad_source=1&gclid=Cj0KCQiAs5i8BhDmARIsAGE4xHyZndsp3CxcVYs5wPG6lw-ZiXpvWt3MDlnWfmCOzbMKWDkZExP7_5saAmmgEALw_wcB>`_ screenshot tests to fail or adds new screenshot tests, please ensure you follow the below instructions to merge the new screenshot tests into the default branch:


**Before merge:**

* Resolve the change on applitools by, creating a new baseline for test (same as old workflow).
* Verify that tests should now pass.


**After merge:**

* Go to https://eyes.applitools.com/app/merge/

* Set Target branch to default

* Set Source branch to the PR's branch

* Click compare

* Select all changes

* Click merge


If the screenshot tests for other PRs begin to fail or are still failing:

* Go to https://eyes.applitools.com/app/baselines

* Find the branch for the other
