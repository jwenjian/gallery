#!/usr/bin/python
# -*- coding: utf-8 -*-
import codecs
import os
import time
from os.path import exists

import requests
from PIL import Image
from github import Github
from github.Issue import Issue
from github.Repository import Repository

'''
github
'''
user: Github
github_repo_env = os.environ.get('GITHUB_REPOSITORY')
username: str = github_repo_env[0:github_repo_env.index('/')]
gallery_repo: Repository


def generate_html_file(articles, update_time):
    global github_repo_env
    with codecs.open('index.html.template', 'r', encoding='utf-8') as t:
        templates = t.read()
        result = templates.format(github_repo_env, articles, update_time)
        t.close()
        with codecs.open('docs/index.html', 'w', encoding='utf-8') as f:
            f.writelines(result)
            f.flush()
            f.close()


def login():
    global user, username
    password = os.environ.get('GITHUB_PERSONAL_TOKEN')
    user = Github(username, password)


def get_gallery_repo():
    global gallery_repo
    gallery_repo = user.get_repo(os.environ.get('GITHUB_REPOSITORY'))


def parse_body(body: str):
    sections = body.replace('\r', '').replace('\n', '').split('---')
    img_section = sections[1]
    # ![<image title>](<image url>)
    return img_section[img_section.index('](') + 2:-1], sections[0]


def download_and_gen_thumbnail_and_upload(image_url: str, issue_id: int):
    full_img_file = 'docs/static/images/fulls/{}.jpg'.format(issue_id)
    thumb_img_file = 'docs/static/images/thumbs/{}.jpg'.format(issue_id)
    with requests.get(image_url) as resp:
        with open(full_img_file, mode='wb') as f:
            f.write(resp.content)
            f.flush()
            f.close()
            img = Image.open(full_img_file)
            bg = Image.new('L', img.size, 0)
            bg.paste(img, (0,0), img)
            bg.thumbnail((240, 320))
            bg.save(thumb_img_file)


def issue_to_article(i: Issue):
    global username, github_repo_env
    # user must be repo owner
    if i.user.login != username:
        return ''

    # get image url
    image_url, desc = parse_body(i.body)

    # if already exists, skip image download, upload
    if not exists('docs/static/images/thumbs/{}.jpg'.format(i.number)) or not exists(
            'docs/static/images/fulls/{}.jpg'.format(i.number)):
        download_and_gen_thumbnail_and_upload(image_url, i.number)

    return '''
    <article>
      <a class="thumbnail" href="https://cdn.jsdelivr.net/gh/{0}/docs/static/images/fulls/{1}.jpg">
        <img src="https://cdn.jsdelivr.net/gh/{0}/docs/static/images/thumbs/{1}.jpg" alt="" />
      </a>
      <h2>{2}</h2>
      <p>{3}</p>
    </article>
    '''.format(github_repo_env, i.number, i.title, desc)


def bundle_articles():
    global gallery_repo
    _repo: Repository = gallery_repo
    issues = _repo.get_issues()
    if not issues:
        return ''
    result = ''
    for i in issues:
        article = issue_to_article(i)
        result += article

    return result


def execute():
    # common
    cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # 1. login
    login()

    # 2. get gallery_repo
    get_gallery_repo()

    # 3. generate articles
    articles = bundle_articles()

    # 4. generate html file
    generate_html_file(articles, cur_time)

    print('index.html updated successfully!!!')


if __name__ == '__main__':
    execute()
