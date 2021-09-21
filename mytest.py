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

    result = i.send_metadata_by_sample_id(a_metadata(), samp_id)
    print(result)


# This is called when the program is run for the first time
if __name__ == "__main__":
    main()

"""
have a way to pick which upload machine is used with auto uploads


"""
