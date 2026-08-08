import urllib.request, os
os.makedirs("replays", exist_ok=True)
urls = [
    ("https://storage.googleapis.com/kagglesdsdata/datasets/11521846/18661776/90045719.json?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcp-kaggle-com%40kaggle-161607.iam.gserviceaccount.com%2F20260808%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20260808T171456Z&X-Goog-Expires=259200&X-Goog-SignedHeaders=host&X-Goog-Signature=9175d75677508afb0b59cc4b7a0c1c1c7b63cbcc00df35763bf63c84bc3075397ee35cccf815c722a387de1c52c9f1fca510deda40d68345ffa4abf7dd0bb9c46f3130c61c2890f5dbaa08be5a84ed2ce1563840517678ea22c282ee634258cf4997e00ece0c662583fafb40a9f4d8f3ab9059b3b9fdc68082dfa33e543e6e29f5fb62d03218c5294286965b4d8d95c2b63943d81718083970cfaad262e0178e7838dea9ebb8b0c0a725584ba8cb5da2cdf7d23749a90966ba17dc4e04cbe936ef71bfb1b6354270c7441bdce20e5720ec2706afbd7235d6473523cac08d7c92c3ca5e912cb817df63cb5cdcae240229c711b182659c133f09a62c3b8a963f7f", "replays/ep_90045719.json"),
    ("https://storage.googleapis.com/kagglesdsdata/datasets/11551024/18714349/90563876.json?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcp-kaggle-com%40kaggle-161607.iam.gserviceaccount.com%2F20260808%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20260808T171456Z&X-Goog-Expires=259200&X-Goog-SignedHeaders=host&X-Goog-Signature=7181915bb9daa8af6606db149eb6aafcadaf92ea69c0191ccb6939f1fb6d899fa35f1d1e4cf0b76280f7deda4529ade3c71d517af3056cf827a6ce44cfa207eb4de8b973a74ef8e4bc5f3adbe1d0925c2a094e0f1a93c9bb0de3228f194fb702942bc2a5dacba2505324d2a4148217743b41b8ae33f067887c1eb62d65654f34138de9d7d73390932080d4e14b48dfcaa2ad96d63806c7fb003901b7917be032ae83f74977b1f4c8ecee2857084ff98cfd37443fb67b4c075170d2ff0d13b45dc810505e123ede150af331ad1fad275a60286620d312ddcf33137c093178f43ca1dfc2e8c6242355b310b75f8512c929de3ec04814c13f5c4985bf30b9123bcf", "replays/ep_90563876.json"),
]
for url, path in urls:
    print(f"Downloading {path}...")
    urllib.request.urlretrieve(url, path)
    print(f"  {os.path.getsize(path)} bytes")
print("Done")
