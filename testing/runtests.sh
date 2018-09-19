

if [ -z $1 ]; then
  echo "Usage: $0 <username> <token>"
  exit 1  
fi

if [ -z $2 ]; then
  echo "Usage: $0 <username> <token>"
  exit 1
fi

export USERNAME=$1
export TOKEN=$2

ls Test_*.py | while read testfile
do
  python3 Test_*.py
done

echo "Running cleanup..."
python3 Post_Cleanup.py
