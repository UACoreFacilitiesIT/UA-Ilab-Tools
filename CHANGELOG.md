# Changelog

All notable changes to this project can be found here.
The format of this changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

#### 2024/06/27 [2.1.2](https://github.com/UACoreFacilitiesIT/UA-Ilab-Tools)

Begins updating repo to current versions of Python.

Introduces Poetry as a dependency manager.

- Because of the time difference between this update and the last one, we have a few deprecation issues. We need to refactor the test script to no longer use nose. And in the meantime, we need this script to move to Python 3.12. This release is the first attempt to do so, and future releases will have updates and finish this process.


#### 2022/4/05 [2.1.1](https://github.com/UACoreFacilitiesIT/UA-Ilab-Tools)

Added ability to specify the date to start your search for service requests.

- The default iLab date range is two years from the current date. If you're trying to find service requests from outside of this date range, you need to specify the date specifically. This has been added to the get_service_requests function in ua_ilab_tools.py as an argument with a default value of 2015. You can override this default if you need a smaller or larger date range.

#### 2021/1/20 [2.1.0](https://github.com/UACoreFacilitiesIT/UA-Ilab-Tools)

Updated setup.py dependencies to be more explicit and contain every dependency.

Added some unreleased code which makes the characters we santize in text dynamically set.

- Previously some dependencies were not listed, but were assumed to be installed through other packages.

- Different iLab cores may require different characters to be removed from form information, and so there is not an update_globals function which allows a program to set the characters to be sanitized dynamically.

#### 2020/2/20 [2.0.2](https://github.com/UACoreFacilitiesIT/UA-Ilab-Tools)

Removed double headed management of forms.

- Was previously checking for both form names which have no samples and if the form itself has no samples. This is redundant, and was changed to only check if a form has no samples.

#### 2020/2/18 [2.0.1](https://github.com/UACoreFacilitiesIT/UA-Ilab-Tools)

Added sample duplication capabilities and added new form type to skip.

- If a radio button on the iLab custom form was checked to duplicate the samples, those samples are duplicated and have A and B appended to their names.

- Forms with ".*NQ.*" in their name are now skipped.

#### 2019/11/26 [2.0.0](https://github.com/UACoreFacilitiesIT/UA-Ilab-Tools)

- Now use new generic rest api.

#### 2019/10/03 [1.0.2](https://github.com/UACoreFacilitiesIT/UA-Ilab-Tools/7db70f277f2160b302bf32b2a795215756d34dc2)

Fixed a bug where the skippable form names weren't being skipped.

- The logic was pretty rigid for what forms should be skipped. Instead of making a giant list that is very brittle, the skip form list is now a list of patterns. Now, if it matches a pattern (e.g. r'Request A Quote.*' matching 'Request A Quote NGS'), it will be skipped.

#### 2019/10/03 [1.0.1](https://github.com/UACoreFacilitiesIT/UA-Ilab-Tools/commit/db56bca84a2206e23842a1533307d73930532514)

A readme was added to the repo, and a next-page bug was fixed.

- Added a README.md file.
- If a next-page item existed in the ilab_tools methods' gets, it wasn't being returned. Now it returns the resources from all of the pages.

#### 2019/10/03 [1.0.0](https://github.com/UACoreFacilitiesIT/UA-Ilab-Tools/commit/bb31724b3cb92370a02dab0fd42d30705e62bbcf)

This is the initial start point for a the University of Arizona Ilab Tools code.

- Moved repo from private repo to public.
