import requests
import json
from datetime import datetime


class WordPressPosts:
    def __init__(self):
        self.base_url = "https://gwen.at/wp-json/wp/v2"
        self.auth = ('gwen', 'gpOO cEeS ANvU yCt9 BAat tHXW')

    def list_posts(self):
        """List all posts with their IDs and titles"""
        endpoint = f"{self.base_url}/posts"
        params = {
            'per_page': 100,  # Maximum posts per request
            '_fields': 'id,title'  # Only get these fields
        }

        response = requests.get(
            endpoint,
            auth=self.auth,
            params=params
        )

        if response.status_code == 200:
            posts = response.json()
            print("\nListe aller Posts:")
            print("-" * 50)
            for post in posts:
                print(f"ID: {post['id']:5} | Titel: {
                      post['title']['rendered']}")
            return posts
        else:
            print(f"Error getting posts: {response.status_code}")
            return None

    def show_post(self, post_id):
        """Show a specific post by its ID"""
        endpoint = f"{self.base_url}/posts/{post_id}"
        response = requests.get(endpoint, auth=self.auth)
        if response.status_code == 200:
            post = response.json()
            print("\nPost:")
            print("-" * 50)
            print(f"ID: {post['id']}")
            print(f"Titel: {post['title']['rendered']}")
            print(f"Status: {post['status']}")
            print(f"Erstellt am: {post['date_gmt']}")
            print("\nInhalt:")
            print(post['content']['rendered'])
            print("\n")
            return post
        else:
            print(f"Error getting post: {response.status_code}")
            return None

    def create_test_post(self):
        """Create a test post and return its ID"""
        endpoint = f"{self.base_url}/posts"

        title = f"Test Post {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        content = f"""
        Dies ist ein Test-Post.
        Erstellt am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        Dieser Artikel wurde automatisch via API erstellt.
        """

        post_data = {
            'title': title,
            'content': content,
            'status': 'draft'
        }

        response = requests.post(
            endpoint,
            json=post_data,
            auth=self.auth,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 201:
            post_id = response.json()['id']
            print(f"\nTest-Post erstellt:")
            print(f"Post ID: {post_id}")
            print(f"Titel: {title}")
            print(f"Status: {response.json()['status']}")
            print(
                f"Edit Link: https://gwen.at/wp-admin/post.php?post={post_id}&action=edit")
            return post_id
        else:
            print(f"Error creating post: {response.status_code}")
            print(response.text)
            return None


def main():
    wp = WordPressPosts()

    while True:
        print("\nWordPress Post Manager")
        print("1. Liste alle Posts")
        print("2. Zeige Post")
        print("3. Erstelle Test-Post")
        print("q. Beenden")

        choice = input("\nWählen Sie eine Option (1-3): ")

        if choice == "1":
            wp.list_posts()
        if choice == "2":
            input_id = input("Geben Sie die Post-ID ein: ")
            post_id = int(input_id)
            wp.show_post(post_id)
        elif choice == "3":
            post_id = wp.create_test_post()
        elif choice == "q":
            break
        else:
            print("Ungültige Option. Bitte wählen Sie 1-3.")


if __name__ == "__main__":
    main()
