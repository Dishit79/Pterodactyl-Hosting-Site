import requests
import json
from dispydactyl import PterodactylClient
import pymongo
from pymongo import MongoClient


cluster = MongoClient('---')
collection = cluster['DisCloud']['info']

class ApiConnection(object):
    client = PterodactylClient('https://panel.disanime.ml/', '---')

    def set_password(self, user, password):
        try:
            data = self.client.user.create_user(user.id, user.email, user.name,  user.discriminator, external_id=str(user.id), password=password, root_admin=False, language='en')
        except:
            data = self.client.user.get_user_info(external_id=user.id)
        try:
            collection.insert_one({'_id':user.id,'plan':'Freemium','server':2,'ram':128,'disk':2000,'cpu':50,'user_id':data['attributes']['id']})
        except:
            collection.update_one({'_id':user.id},{'plan':'Freemium','server':2,'ram':128,'disk':2000,'cpu':50,'user_id':data['attributes']['id']})

    def reset_password(self, user, password):
        e = self.get_user(user)['attributes']
        self.client.user.edit_user(user_id=e['id'],username=e['username'],email=e['email'],first_name=e['first_name'],last_name=e['last_name'],external_id=str(user.id),root_admin=e['root_admin'], password=password)


    def create_server_user(self, user, data):
        user_data = collection.find_one({"_id":user.id})
        user_id = user_data['user_id']

        eggs_data=self.get_egg()
        nodes_data=self.get_nodes()
        egg = None
        nest = None
        node= []

        for key in eggs_data:
            if key['name'] == data['eggs']:
                egg = key['id']
                nest = key['nest']
                break
        for key in nodes_data:
            if key['name'] == data['nodes']:
                node.append(key['id'])
                break
        self.client.servers.create_server(name=data['sname'], user_id=user_id, nest_id=int(nest),egg_id=int(egg),memory_limit=data['ram'], swap_limit=0,disk_limit=data['disk'], location_ids=node,cpu_limit=data['cpu'],backups=3)


    def get_resource(self, user):
        ram = 0
        cpu = 0
        disk = 0

        collection.find_one({"_id":user.id})
        my_servers = self.client.servers.list_servers()
        output_dict = [x for x in my_servers['data']['data'] if x['attributes']['user'] == collection.find_one({"_id":user.id})['user_id']]

        server = (len(output_dict))
        for i in output_dict:

            ram += (i['attributes']['limits']['memory'])
            disk += (i['attributes']['limits']['disk'])
            cpu += (i['attributes']['limits']['cpu'])

        limit = collection.find_one({"_id":user.id})

        final_ram = limit['ram']-ram
        final_cpu = limit['cpu']-cpu
        final_disk = limit['disk']-disk
        final_server = limit['server']-server

        return ({'used':{'ram':ram,'cpu':cpu,'disk':disk,'server':server},'left':{'ram':final_ram,'cpu':final_cpu,'disk':final_disk}})


    def get_server(self, user):
        collection.find_one({"_id":user.id})
        my_servers = self.client.servers.list_servers()
        output_dict = [x for x in my_servers['data']['data'] if x['attributes']['user'] == collection.find_one({"_id":user.id})['user_id']]

        data = []
        for i in output_dict:
            egg = self.client.nests.get_egg_info(i['attributes']['nest'],i['attributes']['egg'])
            node = self.client.nodes.get_node_info(i['attributes']['node'])

            e = {'data':i, 'node':node,'egg':egg}

            data.append(e)

        return (data)


    def get_egg(self):
        list =[]

        all_nests = self.client.nests.list_nests()
        nests = (i['attributes']['id'] for i in all_nests['data']['data'])

        for num in nests:
            inv_nest = self.client.nests.get_eggs_in_nest(num)
            group = [{'name':packets['attributes']['name'], 'id': packets['attributes']['id'], 'nest': num} for packets in inv_nest['data']]
            list.extend(group)

        return (list)


    def get_nodes(self):
        all_nodes = self.client.nodes.list_nodes()

        group = [{'name':packets['attributes']['name'], 'id': packets['attributes']['id']} for packets in all_nodes['data']['data']]

        return (group)

    def get_user(self,user):
        try:
            data = self.client.user.get_user_info(external_id=user.id)
        except:
            e = collection.find_one({"_id":user.id})
            data = self.client.user.get_user_info(e['user_id'])
        return (data)
