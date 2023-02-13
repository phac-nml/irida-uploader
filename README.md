# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/phac-nml/irida-uploader/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                               |    Stmts |     Miss |   Cover |   Missing |
|------------------------------------------------------------------- | -------: | -------: | ------: | --------: |
| iridauploader/\_\_init\_\_.py                                      |        1 |        0 |    100% |           |
| iridauploader/api/\_\_init\_\_.py                                  |        2 |        0 |    100% |           |
| iridauploader/api/api\_calls.py                                    |      420 |      110 |     74% |95, 98-100, 133-134, 178-182, 198-204, 217-229, 243, 249, 254, 262, 283-284, 289, 301-306, 310, 314, 337-338, 390-391, 399, 417-418, 427, 454-455, 464, 476-491, 518-519, 524-525, 548-549, 554-556, 572-573, 578, 623-625, 630-631, 653-661, 691-709, 842-843, 848-850, 869-870, 875-877, 950-951, 956-958, 982-993 |
| iridauploader/api/exceptions/\_\_init\_\_.py                       |        4 |        0 |    100% |           |
| iridauploader/api/exceptions/file\_error.py                        |        2 |        0 |    100% |           |
| iridauploader/api/exceptions/irida\_connection\_error.py           |        2 |        0 |    100% |           |
| iridauploader/api/exceptions/irida\_resource\_error.py             |       12 |        3 |     75% |21, 25, 28 |
| iridauploader/api/exceptions/irida\_upload\_canceled\_exception.py |        2 |        0 |    100% |           |
| iridauploader/config/\_\_init\_\_.py                               |        1 |        0 |    100% |           |
| iridauploader/config/config.py                                     |      141 |       30 |     79% |66-86, 97-98, 102-104, 118-120, 149-150, 245-249, 259, 262 |
| iridauploader/core/\_\_init\_\_.py                                 |        3 |        0 |    100% |           |
| iridauploader/core/api\_handler.py                                 |      116 |        0 |    100% |           |
| iridauploader/core/cli.py                                          |      114 |       86 |     25% |32-118, 127-197, 216-222, 234-235, 239-242, 277 |
| iridauploader/core/exit\_return.py                                 |       14 |        1 |     93% |        28 |
| iridauploader/core/file\_size\_validator.py                        |       19 |        0 |    100% |           |
| iridauploader/core/logger.py                                       |       38 |        2 |     95% |     62-63 |
| iridauploader/core/model\_validator.py                             |       42 |       10 |     76% |47-54, 66-67, 72, 99 |
| iridauploader/core/parsing\_handler.py                             |       45 |        0 |    100% |           |
| iridauploader/core/uniform\_file\_count\_validator.py              |       14 |        0 |    100% |           |
| iridauploader/core/upload.py                                       |      132 |        9 |     93% |144-145, 151-152, 172, 190, 194, 234-242 |
| iridauploader/core/upload\_helpers.py                              |      117 |        0 |    100% |           |
| iridauploader/model/\_\_init\_\_.py                                |        8 |        0 |    100% |           |
| iridauploader/model/directory\_status.py                           |      144 |        8 |     94% |102, 129, 140, 153-155, 162, 199 |
| iridauploader/model/exceptions/\_\_init\_\_.py                     |        1 |        0 |    100% |           |
| iridauploader/model/exceptions/model\_validation\_error.py         |       12 |        0 |    100% |           |
| iridauploader/model/metadata.py                                    |       32 |       16 |     50% |12-16, 20, 24, 28, 32, 36, 40, 43, 46-49 |
| iridauploader/model/project.py                                     |       34 |        0 |    100% |           |
| iridauploader/model/sample.py                                      |       61 |        0 |    100% |           |
| iridauploader/model/sequence\_file.py                              |       25 |        0 |    100% |           |
| iridauploader/model/sequencing\_run.py                             |       33 |        0 |    100% |           |
| iridauploader/model/validation\_result.py                          |       12 |        0 |    100% |           |
| iridauploader/parsers/\_\_init\_\_.py                              |        5 |        0 |    100% |           |
| iridauploader/parsers/base\_parser.py                              |        8 |        0 |    100% |           |
| iridauploader/parsers/common.py                                    |       43 |        0 |    100% |           |
| iridauploader/parsers/directory/\_\_init\_\_.py                    |        1 |        0 |    100% |           |
| iridauploader/parsers/directory/parser.py                          |       75 |       26 |     65% |100-109, 114, 117-124, 128-136, 144-147 |
| iridauploader/parsers/directory/sample\_parser.py                  |      102 |        1 |     99% |       213 |
| iridauploader/parsers/directory/validation.py                      |       32 |        0 |    100% |           |
| iridauploader/parsers/exceptions/\_\_init\_\_.py                   |        5 |        0 |    100% |           |
| iridauploader/parsers/exceptions/directory\_error.py               |       10 |        0 |    100% |           |
| iridauploader/parsers/exceptions/file\_size\_error.py              |       12 |        3 |     75% |17, 21, 24 |
| iridauploader/parsers/exceptions/sample\_sheet\_error.py           |       12 |        3 |     75% |20, 24, 27 |
| iridauploader/parsers/exceptions/sequence\_file\_error.py          |        8 |        2 |     75% |    17, 20 |
| iridauploader/parsers/exceptions/validation\_error.py              |       12 |        1 |     92% |        26 |
| iridauploader/parsers/miniseq/\_\_init\_\_.py                      |        1 |        0 |    100% |           |
| iridauploader/parsers/miniseq/parser.py                            |       79 |        6 |     92% |154-155, 161-164 |
| iridauploader/parsers/miniseq/sample\_parser.py                    |      131 |       11 |     92% |54-55, 61-62, 82-83, 150, 259-262, 279 |
| iridauploader/parsers/miniseq/validation.py                        |       42 |        1 |     98% |        69 |
| iridauploader/parsers/miseq/\_\_init\_\_.py                        |        1 |        0 |    100% |           |
| iridauploader/parsers/miseq/parser.py                              |       75 |       10 |     87% |142-143, 149-152, 162-165 |
| iridauploader/parsers/miseq/sample\_parser.py                      |      123 |       11 |     91% |58-59, 65-66, 72-73, 86-87, 246-249 |
| iridauploader/parsers/miseq/validation.py                          |       42 |        1 |     98% |        70 |
| iridauploader/parsers/nextseq2k\_nml/\_\_init\_\_.py               |        1 |        0 |    100% |           |
| iridauploader/parsers/nextseq2k\_nml/parser.py                     |       75 |       10 |     87% |142-143, 149-152, 162-165 |
| iridauploader/parsers/nextseq2k\_nml/sample\_parser.py             |      118 |        9 |     92% |42-43, 49-50, 64-65, 225-228 |
| iridauploader/parsers/nextseq2k\_nml/validation.py                 |       42 |        1 |     98% |        69 |
| iridauploader/parsers/nextseq/\_\_init\_\_.py                      |        1 |        0 |    100% |           |
| iridauploader/parsers/nextseq/parser.py                            |       56 |        8 |     86% |108-111, 118-121 |
| iridauploader/parsers/nextseq/sample\_parser.py                    |      142 |       11 |     92% |58-59, 65-66, 86-87, 112, 143, 278-281 |
| iridauploader/parsers/nextseq/validation.py                        |       42 |        0 |    100% |           |
| iridauploader/parsers/parsers.py                                   |       20 |        1 |     95% |        48 |
| iridauploader/progress/\_\_init\_\_.py                             |        3 |        0 |    100% |           |
| iridauploader/progress/exceptions/\_\_init\_\_.py                  |        1 |        0 |    100% |           |
| iridauploader/progress/exceptions/directory\_error.py              |       10 |        0 |    100% |           |
| iridauploader/progress/upload\_signals.py                          |       28 |       10 |     64% |11, 25, 29, 33, 41-48, 54 |
| iridauploader/progress/upload\_status.py                           |       74 |       11 |     85% |74, 77-84, 101, 145, 157-158 |
|                                                          **TOTAL** | **3035** |  **412** | **86%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/phac-nml/irida-uploader/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/phac-nml/irida-uploader/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/phac-nml/irida-uploader/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/phac-nml/irida-uploader/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fphac-nml%2Firida-uploader%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/phac-nml/irida-uploader/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.