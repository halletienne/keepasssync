#!/usr/bin/env python3

from kppy.database import KPDBv1
from kppy.exceptions import KPError
import sys, os, time





def openDatabase(db_path,db_pass):
    '''
    Check if databases file exist and open it as read only
    Return the database
    '''

    if len(db_pass)==0:
        db_pass=input('Enter password for '+db_path+' :')

    try:
        # Check if file exist, raise an exception if not
        if not os.path.isfile(db_path):
            raise FileNotFoundError(db_path)


        db = KPDBv1(db_path, db_pass, read_only = True) 
        
    # Execption Handler for the kppy opener
    except KPError as err :
        print(err)
        print('Error while opening '+db_path)
        print('Quitting...')
        quit()

    except FileNotFoundError :
        print('No File found at '+db_path)
        print('Quitting...')
        quit()

    return db

def splitPath(path):
    '''
    Split a path:password string in two if needed
    Return a tuple dp_path,db_pass
    '''

    # Remember the format is path:password
    i=path.find(':')

    if i != -1 :
        db_path=path[:i]
        db_pass=path[i+1:]
    else :
        db_path=path
        # Empty pass
        db_pass=''

    return (db_path,db_pass)

def help():
    '''
    Help Message to print out when a wrong action is done
    '''
    print('\n=============\n\
keepasssync needs two database paths : \n \
\t keepasssync.py /path/to/db1.kdb[:Password1] /path/to/db2.kdb[:Password2]  [/path/to/NewDB.kdb[:NewPassword]] \n ')
    quit()


def cleanGroupAdd(db,group):
    # KeepassX sometimes put an image=0, kppy does not accept it
    group_image=group.image
    if group_image == 0 :
        group_image +=1

    # Check if the group as a parent or not
    if group.level==0 :
        db.create_group(title=str(group.title),image=group_image)
    else :
        db.create_group(title=group.title,image=group_image,parent=group.parent)

    return db

def cleanDb(db):
    # Because wit kppy a group is automatically created, called Internet, let's remove it, if empty
    internet_group = [item for item in db.groups if item.title == 'Internet'][0] 
    if len(internet_group.entries) == 0 :
        print('\nDelete empty Internet Group')
        internet_group.remove_group()

    return db


def syncDb(dbnew,db1,db2):
    '''
    Firstly add the first db's groups to the new db
    Then add the second db's groups and checking if it is not already there
    Take as argument :
        - the db to ammend
        - the list of group from the first db
        - the list of group from the second db
    Returns the DB modified
    '''

    # Syncing groups
    list_group1=db1.groups
    list_group2=db2.groups

    correspondance1=[]
    ids_group1=[]
    # Adding the group from the first list to the new DB
    print('Starting to add groups from first DB')

    for group in list_group1 : 
        print('Group to add:"'+group.title+'"\tID : '+str(group.id_)+ '\t\tLevel:'+str(group.level)+'\timage:'+str(group.image)+'\ttype image:'+str(type(group.image)))
        cleanGroupAdd(dbnew,group)
        
        # Append to a list the id of the group just added
        ids_group1.append(group.id_)
        correspondance1.append((dbnew.groups[len(dbnew.groups)-1],group))

    
    correspondance2=[]
    # Adding the group from the second list to the DB
    print('\nStarting to add groups from second DB')
    for group in list_group2 :
        print('\nGroup title to add:"'+group.title+'"\tID : '+str(group.id_)+ '\t\tLevel:'+str(group.level)+'\timage:'+str(group.image)+'\ttype image:'+str(type(group.image)))
        # Check if already present
        if group.id_ not in ids_group1 :
            # Not present
            print('\t [+] Not present !')
            cleanGroupAdd(dbnew,group)
            correspondance2.append((dbnew.groups[len(dbnew.groups)-1],group))
        else :
            # already present
            print('\t [-] Group already exists')
            #[group1 for group1 in correspondance1 if group.id_==group1[1].group.id_][0][0]
            # Have to find the already added group in correspondance1
            correspondance2.append(([group1 for group1 in correspondance1 if group.id_==group1[1].id_][0][0] ,group))
            #correspondance2.append((dbnew.groups[len(dbnew.groups)-1],group))

    #input('Check the group creation')



    # Syncing entries
    ids_entries=[]
    list_entries1=db1.entries
    list_entries2=db2.entries

    for entry in list_entries1 :
        if entry.title != 'Meta-Info':
            ids_entries.append(entry.uuid)
            print('\nKey :'+entry.group.title+'/'+entry.title)
            print('\t[+] Adding key ')

            # Find corresponding group
            #[item for item in a if item[1] == entry.group][0][0]
            # This line find the corresponding group of the new DB from the correspondance1 list
            dbnew.create_entry(group=[item for item in correspondance1 if item[1] == entry.group][0][0],title=entry.title,image=entry.image,url=entry.url,username=entry.username,password=entry.password,comment=entry.comment)

    print ('\n\nAdding second entry list\n\n')
    for entry in list_entries2 : 
        if entry.title != 'Meta-Info':
            print('\nKey :'+entry.group.title+'/'+entry.title)
            if entry.uuid in ids_entries:
                print('[!] Key existing ')
                # Getting the similar entry from the first DB
                entry_dup=[item for item in db1.entries if item.uuid == entry.uuid][0]

                # Comparing expiracy date
                if entry_dup.last_mod >= entry.last_mod :
                    print('\t[=] Keeping the first key (same date or older)')
                else :
                    print('\t[<] Changing to second key')
                    # Should delete the old one and add the new one
                    # Deleting the old key
                    print('\t\t[-] Deleting old key')
                    dbnew.remove_entry([item for item in dbnew.entries if item.title == entry.title and item.username == entry.username ][0])
                    # Adding the new key
                    print('\t\t[+] Adding new key')
                    dbnew.create_entry(group=[item for item in correspondance2 if item[1] == entry.group][0][0],title=entry.title,image=entry.image,url=entry.url,username=entry.username,password=entry.password,comment=entry.comment)

            else :
                print('[!] Key not existing')
                print('\t[+] Adding key ')
                dbnew.create_entry(group=[item for item in correspondance2 if item[1] == entry.group][0][0],title=entry.title,image=entry.image,url=entry.url,username=entry.username,password=entry.password,comment=entry.comment)

    return dbnew






#####
####
# Starting Here
###
####

if len(sys.argv)<=2 :
    print('Not enough arguments....')
    help()
elif len(sys.argv)>4 :
    print('Too many arguments...')
    help()

elif len(sys.argv)==3 :
    # Naming the new db after the epoch
    dbnew_path=os.getcwd()+'/merged_'+str(int(time.time()))+'.kdb'
    print('The merged DB will be found at: '+dbnew_path)
    dbnew_pass=input('Enter the new password')

else :
    dbnew_path, dbnew_pass = splitPath(sys.argv[3])
    if len(dbnew_pass)==0:
        dbnew_pass=input('Enter password for '+dbnew_path+' :')


# Splitting the path form the pass
db1_path, db1_pass = splitPath(sys.argv[1])
db2_path, db2_pass = splitPath(sys.argv[2])

# Opening the database in readonly mode
db1=openDatabase(db1_path, db1_pass)
db2=openDatabase(db2_path, db2_pass) 


db1.load()
db2.load()



#### Test
#new_group_list=db1.groups+db2.groups
#print('Print the list  of groups')
#for group in new_group_list :
#    print(group.title,group.id_,group.db)
#    group.db=None 
#
#new_group_set=set(new_group_list)
#print('Print the set of groups')
#
#for group in new_group_set :
#    print(group.title,group.id_,group.db)
## Creating the new database
dbnew=KPDBv1(filepath=dbnew_path, password=dbnew_pass,  read_only=False, new=True)

# Creating the group architecture
dbnew=syncDb(dbnew,db1,db2)

dbnew = cleanDb(dbnew)







dbnew.save()
dbnew.close()
db1.close()
db2.close()

print('\nSync went good :D ')
