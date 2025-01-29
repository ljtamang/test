mkdir my-repo
cd my-repo
git init
git config core.sparseCheckout true
git remote add origin https://github.com/username/repository.git
echo "products/*" >> .git/info/sparse-checkout
git pull origin master
