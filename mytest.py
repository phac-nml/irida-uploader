from iridauploader import api, model

client_id = "sequencer"
client_secret = "N9Ywc6GKWWZotzsJGutj3BZXJDRn65fXJqjrk29yTjI"
base_url = "http://localhost:8080/api/"
username = "admin"
password = "password1"

proj_id = 102
samp_name = "my_sample"


def a_sample():
    s = model.Sample(samp_name)
    return s


def a_metadata():
    m = model.Metadata({"some": "data",
                        "is": "here"})
    return m


def main():
    i = api.ApiCalls(client_id, client_secret, base_url, username, password)

    # result = i.send_sample(a_sample(), proj_id)
    samp_id = i.sample_exists(samp_name, proj_id)
    print(samp_id)

    # result = i.send_metadata_by_sample_id(a_metadata(), samp_id)
    # print(result)

    result = i.get_assemblies_files_by_sample_id(samp_id)
    print(result)

# This is called when the program is run for the first time
if __name__ == "__main__":
    main()

"""
have a way to pick which upload machine is used with auto uploads


"""
"""
if passing:
    # Check that sample exists and make it if not
    sample_id = api_instance.sample_exists(sample_name=sample_name, project_id=project_id)
    if not sample_id:
        irida_sample = model.Sample(sample_name=sample_name)
        sample_id = api_instance.send_sample(sample=irida_sample, project_id=project_id)
        if not sample_id:
            raise Exception("something here")

    upload_metadata = model.Metadata(metadata=metadata, project_id=project_id, sample_name=sample_name)
    status = api_instance.send_metadata(upload_metadata, sample_id )

    print(status, '\n')
"""
"pip install rauth requests chardet appdirs cerberus argparse requests-toolbelt"