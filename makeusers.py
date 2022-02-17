from iridauploader.api import ApiCalls
api = ApiCalls("seqqq", "AQ4oHSYJdqBKZZ4T3JC8DhyDtsDd7CapIHcqJojoks","http://localhost:8080/api/","admin","Password1!")

base_username = "scriptuser"
project_id = 186


def create_and_add_to_project(username, project):
    print("Creating: " + username)
    res = api.create_user(username)
    # ex = {'resource': {'username': 'new_user_2', 'email': 'new_user_2@mail.server', 'firstName': 'user', 'lastName': 'name', 'phoneNumber': '5555555555', 'enabled': True, 'systemRole': 'ROLE_USER', 'createdDate': '2022-02-16T17:16:36.000Z', 'modifiedDate': '2022-02-16T17:16:36.000Z', 'locale': 'en', 'label': 'user name', 'links': [{'rel': 'user/projects', 'href': 'http://localhost:8080/api/users/new_user_2/projects'}, {'rel': 'self', 'href': 'http://localhost:8080/api/users/68'}], 'identifier': '68'}}
    # id = res.json()['resource']['identifier']
    # import pdb;pdb.set_trace()
    # print(res)
    print("Adding: " + username)
    res2 = api.add_user_to_project(username, project_id)


for i in range(50000):
    full_username = base_username + str(i)
    create_and_add_to_project(full_username, project_id)

print("Done")
