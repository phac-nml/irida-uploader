
# How to Create a new Release

This document is intended for PHAC-NML developers for use when creating a new official release.

Please follow all steps to ensure the release is the same across github / windows build / pypi

### Git Release
#### Changes

Double check all the code in this release has been merged into development, and the CHANGELOG.md file reflects these changes with an appropriate Version Number update.

Make sure your local development branch is up to date with origin

#### Update Version Number

Execute the following command to update version number in the various build files

    ./scripts/update.sh <X.Y.Z>

For Major updates, that completely break compatibility, update to a new X version

For Feature Updates, update to a new Y version

For Bug Fixes and Minor Updates, update to a new Z version

#### Create a new tag

Create a new tag with the same version number as above

    git tag X.Y.Z

Verify the tag was created

    git tag

Push tag up to origin

    git push origin X.Y.Z

#### Create the release on GitHub

On the Releases page, click "Draft a new release"

In the box that says "Tag version", enter in the tag number you created above. It should indicate that the tag exists.

Give an appropriate release title.

Copy and paste the raw text from your CHANGELOG.md for this release into the description box.

Move onto the Builds section to attach binaries before publishing release.

### Builds

#### Windows Build

If you do not already have `nsis` installed, install it with the following command

    sudo apt install nsis

Create a new windows build by running the following command

    make windows

This will create a new installer in the folder `build/nsis/` with the name `IRIDA_Uploader_GUI_X.Y.Z.exe`

Attach this file to the release and publish.

#### PyPi Release

Before starting, make sure your registered pypi.org account has write access to https://pypi.org/project/iridauploader/

Ensure you have `twine` installed

    python3 -m pip install --user --upgrade twine

Build the wheel and tar.gz files to upload to pypi

    make wheel

They will be made in the `dist/` directory

Then upload them to pypi

    python3 -m twine upload dist/*

Treat yourself to a coffee break (It will take 10-20 minutes until your files will be able to by pulled via pip)

##### Test pulling your new files

Leave the git repo, and create a new virtual environment and test your pypi build

    python3 -m venv testenv
    source testenv/bin/activate
    pip install iridauploader=X.Y.Z

If everything looks to be in order, your PyPi release is complete.

If there are errors that occur during installation, you will need to correct the error, bump the version number for the bug fix and start from the beginning.

### Finally

Pull development into main and push to origin

    git checkout main
    git pull origin main
    git pull origin development
    git push origin main

Congratulations, you have successfully completed a new release of the IRIDA Uploader.