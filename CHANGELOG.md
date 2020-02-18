# Changelog

All notable changes to this project can be found here.
The format of this changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

#### 2020/2/18  [2.0.1](https://github.com/UACoreFacilitiesIT/UA-Ilab-Tools)

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
