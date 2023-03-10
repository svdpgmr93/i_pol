import requests
import json
from static_data import country_dict, sexs
import sqlite3
import os

class RedParser():
    """Filters marks"""
    arest_country_mark = 'arrestWarrantCountryId='
    name_mark = '&name='
    forename_mark = '&forename='
    age_min_mark = '&ageMin='
    age_max_mark = '&ageMax='
    sex_mark = '&sexId='
    base_url = 'https://ws-public.interpol.int/notices/v1/red?'
    url_end = '&resultPerPage=160&page=1'
    parent_folder = 'C:/persons_red'

    @classmethod
    def create_person(cls, urls):
        conn = sqlite3.connect('i_pol.db', timeout=1000)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS red_person (id INTEGER PRIMARY KEY, person_url TEXT NOT NULL UNIQUE)")
        for url in urls:
            try:
                sql = '''INSERT INTO red_person (person_url) VALUES (?)'''
                cursor.execute(sql, (url,))
                cls.get_person_data(url)
            except sqlite3.IntegrityError:
                continue
        conn.commit()
        conn.close()

    @classmethod
    def get_person_data(cls, url):
        if type(url) is str:
            r = requests.get(url)
            data = r.json()
            id = str(data["entity_id"])
            id = id.replace('/','_')
            try:
                os.mkdir(cls.parent_folder)
            except FileExistsError:
                pass
            path = os.path.join(cls.parent_folder, id)
            try:
                os.mkdir(path)
            except FileExistsError:
                pass
            json_name = os.path.join(path, id) + '.json'
            with open(json_name, 'w') as j:
                json.dump(data,j)
            """Comment out the code below to speed up the script during testing. 54-63"""
            img = data['_links']['images']['href']
            img_data = requests.get(img).json()
            try:
                img_link = img_data['_embedded']['images'][0]['_links']['self']['href']
                img_name = os.path.join(path,id) + '.jpg'
                img = requests.get(img_link).content
                with open(img_name, 'wb') as image:
                    image.write(img)
            except IndexError:
                pass
            """Comment out the code above to speed up the script during testing. 54-63"""
        elif type(url) is list or set:
            for elem in url:
                cls.get_person_data(elem)


    @classmethod
    def get_json_from_url(cls, country=0, sex=0, age=0, name=0, forename=0):
        persons = []
        if country :
            url = cls.base_url + cls.arest_country_mark + country
        if sex:
            url += cls.sex_mark + sex
        if age:
            url += cls.age_min_mark + str(age) + cls.age_max_mark + str(age)
        if name:
            url += cls.name_mark + name
        if forename:
            url += cls.forename_mark + forename
        url += cls.url_end
        try:
            r = requests.get(url)
            data = r.json()
            person_in_json = data['total']
        except KeyError as e:
            print('Cathing error ----------', e)
            cls.get_json_from_url(url)
        print(url)
        for person in data['_embedded']['notices']:
            persons.append(person['_links']['self']['href'])
        print('query =', country, sex, age, name, forename, '--- count =', person_in_json)
        return {'persons': persons, 'count' : person_in_json, 'url' : url}

    @classmethod
    def get_persons_url(cls, country=0):
        if country:
            data = cls.get_json_from_url(country=country)
            total_persons_urls = set()
            if data['count'] <= 160:
                print(country, data['count'])
                total_persons_urls = total_persons_urls.union(set(data['persons']))
            else:
                """If count of person > 160 we added a new filter, added filter with sex"""
                for sex in sexs:
                    data = cls.get_json_from_url(country=country, sex=sex)
                    if data['count'] <= 160:
                        print(country, sex, data['count'])
                        total_persons_urls = total_persons_urls.union(set(data['persons']))
                    else:
                        """If count of person > 160 we added a new filter, added filter with age"""
                        for year in range(18, 100):
                            data = cls.get_json_from_url(country=country, sex=sex, age=year)
                            if data['count'] <= 160:
                                print(country,sex, year, data['count'])
                                total_persons_urls = total_persons_urls.union(set(data['persons']))
                            else:
                                """If count of person > 160 we added a new filter, added filter with letter in name"""
                                print('Work with letter', data['count'])
                                count_in_age_set = set()
                                count_in_age = data['count']
                                for letter in range(65,91):
                                    data = cls.get_json_from_url(age=year, country=country, sex=sex, name=(chr(letter)))
                                    if data['count'] <= 160:
                                        total_persons_urls = total_persons_urls.union(set(data['persons']))
                                        count_in_age_set = count_in_age_set.union(set(data['persons']))
                                        print(country, sex, year, chr(letter), data['count'], '--------- count in this age', len(count_in_age_set))
                                        if len(count_in_age_set) == count_in_age:
                                            break
                                    else:
                                        """If count of person > 160 we added a new filter, added second letter in name"""
                                        for fletter in range(65,91):
                                            data = cls.get_json_from_url(age=year, country=country, sex=sex,
                                                                                    name=chr(letter), forename=chr(fletter))
                                            if data['count'] <= 160:
                                                total_persons_urls = total_persons_urls.union(set(data['persons']))
                                                count_in_age_set = count_in_age_set.union(set(data['persons']))
                                                print(country, sex, year, chr(letter), chr(fletter), data['count'], '--------- count in this age', len(count_in_age_set))
                                                if len(count_in_age_set) == count_in_age:
                                                    break
                                    print(country, sex, year, chr(letter), data['count'])
                                total_persons_urls = total_persons_urls.union(count_in_age_set)
        else:
            for country in country_dict:
                cls.get_persons_url(country=country)
        # with open('total_persons_urls.json', 'w') as f:
        #     json.dump(tuple(total_persons_urls), f)
        #     print(len(total_persons_urls))
        cls.get_person_data(total_persons_urls)
        return total_persons_urls


class YellowParser(RedParser):
    arest_country_mark = 'nationality='
    base_url = 'https://ws-public.interpol.int/notices/v1/yellow?'
    parent_folder = 'C:/persons_yellow'

"""I chose these countries (AO - 6 person in Red and AF - 26 person in Yellow) to speed up testing"""
YellowParser.get_persons_url(country='AF')
RedParser.get_persons_url(country='AO')

"""Loading pictures greatly increases the time of work. 
If you need to speed up the tests, you can disable the loading of images. Comment out code lines 54-63"""