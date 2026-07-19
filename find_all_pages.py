import os

for root, dirs, files in os.walk('webcms/admin-ui/src/admin/pages'):
    for f in sorted(files):
        print(os.path.join(root, f))
