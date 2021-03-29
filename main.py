import os
import requests
import json
import time

from io import BytesIO
from urllib.parse import urlparse

from PIL import Image
from dotenv import load_dotenv

BAND_KEY = 'INSERT_BAND_KEY'
API_URL = 'https://openapi.band.us'


def extract_photos(photo_list):
    photo_dir_list = []
    for photo in photo_list:
        res = requests.get(photo['url'])
        img = Image.open(BytesIO(res.content))

        url_info = urlparse(photo['url'])
        path_split = url_info.path.split('/')[1:]

        dir_path = f'./images/{path_split[0]}/{path_split[1]}'

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        save_path = f'{dir_path}/{path_split[2]}'
        img.save(save_path, 'JPEG')

        photo_dir_list.append(save_path)

    return photo_dir_list


load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

base_parameter = {
    'access_token': ACCESS_TOKEN,
    'band_key': BAND_KEY,
}

cur_parameter = base_parameter.copy()

post_list = []
comment_list = []
while True:
    time.sleep(1)

    res = requests.get(
        f'{API_URL}/v2/band/posts',
        params=cur_parameter
    )
    res_dict = json.loads(res.text)

    if res_dict['result_code'] != 1:
        break

    res_dict = res_dict['result_data']

    for item in res_dict['items']:
        cur_post_key = item['post_key']

        #extract photo
        photo_dir_list = []
        photo_dir_list += extract_photos(item['photos'])

        comment_parameter = base_parameter.copy()
        comment_parameter['post_key'] = cur_post_key
        comment_parameter['sort'] = "+created_at"

        comment_raw = requests.get(
            f'{API_URL}/v2/band/post/comments',
            params=comment_parameter
        )
        comment_dict = json.loads(comment_raw.text)

        for comment in comment_dict['result_data']['items']:
            if comment['photo']:
                comment_dir = extract_photos([comment['photo']])
                comment['photo']['url'] = comment_dir[0]

        post_dict = {
            'author': {
                'name': item['author']['name'],
                'user_key': item['author']['user_key'],
            },
            'content': item['content'],
            'created_at': item['created_at'],
            'photo': photo_dir_list,
            'comments': comment_dict['result_data']['items']
        }
        post_list.append(post_dict)

    cur_parameter = res_dict['paging']['next_params']

    if not cur_parameter:
        break

with open('data.json', 'w') as outfile:
    json.dump(post_list, outfile, ensure_ascii=False)
