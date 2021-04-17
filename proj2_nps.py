#################################
##### Name: Muhammed Hamid
##### Uniqname: mdhamid
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key


CACHE_FILENAME = "national_sites_cache.json"
CACHE_DICT = {}

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return f'{self.name} ({self.category}): {self.address} {self.zipcode}'


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''

    state_url_dict = {}
    BASE_URL = "https://www.nps.gov"

    CACHE_DICT = open_cache()

    if BASE_URL in CACHE_DICT.keys():
        val = CACHE_DICT[BASE_URL]
        soup = BeautifulSoup(val, 'html.parser')
        print('Using Cache')
    else:
        response = requests.get(BASE_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        CACHE_DICT[BASE_URL] = response.text
        print('Fetching')

    save_cache(CACHE_DICT)

    all_map_items = soup.find_all("ul", class_="dropdown-menu SearchBar-keywordSearch")
    states_list = all_map_items[0].find_all('a')
    
    for state in states_list:
        state_name = state.contents[0].lower()
        href = state['href']
        state_url_dict[state_name] = BASE_URL + href

    return state_url_dict


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    CACHE_DICT = open_cache()
    
    if site_url in CACHE_DICT.keys():
        val = CACHE_DICT[site_url]
        soup = BeautifulSoup(val, 'html.parser')
        print('Using Cache')
    else:
        response = requests.get(site_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        CACHE_DICT[site_url] = response.text
        print('Fetching')

    save_cache(CACHE_DICT)

    name = soup.find("a", class_="Hero-title").contents[0]
    try:
        category = soup.find("span", class_="Hero-designation").contents[0]

    except:
        category = 'No category'

    try:
        zipcode = soup.find("span", class_="postal-code").contents[0].strip()
    
    except:
        zipcode = 'No zip'

    try:
        address = f'{soup.find("span", itemprop="addressLocality").contents[0]}, {soup.find("span", itemprop="addressRegion").contents[0]}'

    except:
        address = 'No address'

    phone = soup.find("span", class_="tel").contents[0].strip()

    nat_site_instance = NationalSite(category, name, address, zipcode, phone)

    return nat_site_instance




def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''

    
    state_site_url_list = []
    state_site_instance_list = []
    BASE_URL = "https://www.nps.gov"

    CACHE_DICT = open_cache()

    if state_url in CACHE_DICT.keys():
        val = CACHE_DICT[state_url]
        soup = BeautifulSoup(val, 'html.parser')
        print('Using Cache')
    else:
        response = requests.get(state_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        CACHE_DICT[state_url] = response.text
        print('Fetching')

    save_cache(CACHE_DICT)

    site_list_div = soup.find("div", id="parkListResultsArea")
    site_list_li = site_list_div.find_all("li", class_="clearfix")
    for li in site_list_li:
        site_list_h3 = li.find('h3')
        state_site_url_list.append(BASE_URL + site_list_h3.contents[0]['href'])
    

    for site_url in state_site_url_list:
        state_site_instance_list.append(get_site_instance(site_url))

    return state_site_instance_list

def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    base_url = 'http://www.mapquestapi.com/search/v2/radius'
    params = {
        'key': secrets.API_KEY,
        'origin': site_object.zipcode,
        'radius': 10,
        'units': 'm',
        'maxMatches': 10,
        'ambiguities': 'ignore',
        'outFormat': 'json'
    }

    CACHE_DICT = open_cache()

    if site_object.zipcode in CACHE_DICT.keys():
        result_dict = CACHE_DICT[site_object.zipcode]
        print('Using Cache')
    else:
        response = requests.get(base_url, params)
        result = response.json()
        CACHE_DICT[site_object.zipcode] = result
        result_dict = result
        print('Fetching')

    save_cache(CACHE_DICT)

    return result_dict


def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        CACHE_DICT = json.loads(cache_contents)
        cache_file.close()
    except:
        CACHE_DICT = {}
    return CACHE_DICT

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''

    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 

if __name__ == "__main__":


    loop = 1
    exit_var = 0

    while not exit_var:

        back = 1

        while back:

            state = input('\nPlease enter state name or "exit": ')
            state_url_dict = build_state_url_dict()

            if state.lower() == 'exit':
                print('exiting app')
                exit_var = 1
                break

            try:
                if state.lower() in state_url_dict.keys():
                    state_url = state_url_dict[state.lower()]
                    instance_list = get_sites_for_state(state_url)
                else:
                    print('[Error] Please enter a valid state')
                    continue
            except:
                print('\n[Error] This state is not in the record or is an invalid entry, please try again\n')

            if not exit_var:
                site_list = []
                for num, site in enumerate(instance_list):
                    site_list.append(num)
                    if num == 0:
                        print('-------------------------------------------')
                        print(f'List of national sites in {state.lower()}')
                        print('-------------------------------------------')
                    print(f'[{num+1}] {site.info()}')


            inner_loop = 1

            while inner_loop:

                try:

                    list_num = input('\nChoose a number from the above list for which you would like to see nearby places, or type "exit" or "back": ')


                    if list_num == "back" or list_num == "Back":
                        break
                    elif list_num == "exit" or list_num == "Exit":
                        inner_loop = 0
                        back = 0
                        exit_var = 1
                        loop = 0
                    elif int(list_num) > len(site_list):
                        print("[Error] Please choose a number from the above list")
                        continue
                    elif int(list_num) <= len(site_list):
                        for num, site in enumerate(instance_list):
                            if num+1 == int(list_num):
                                near_me = get_nearby_places(site)
                                for num1, location in enumerate(near_me['searchResults']):
                                    name_loc = location['name']
                                    if location['fields']['group_sic_code_name_ext']:
                                        category_loc = location['fields']['group_sic_code_name_ext']
                                    else:
                                        category_loc = 'no category'
                                    if location['fields']['address']:
                                        address_loc = location['fields']['address']
                                    else:
                                        address_loc = 'no address'
                                    if location['fields']['city']:
                                        city_loc = location['fields']['city']
                                    else:
                                        city_loc = 'no city'
                                    if num1 == 0:
                                        print("-------------------------")
                                        print(f'Places near {site.name}')
                                        print("-------------------------")
                                    print(f'- {name_loc} ({category_loc}): {address_loc}, {city_loc}')
                except:
                    print("[Error] Please choose a number from the above list")
        
        