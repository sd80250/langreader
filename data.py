# returns whichever text is more complex or difficult to read
def compare(text1, text2):
    return len(text1) > len(text2)
    
    
# inserts
def insert(poem):
    # data = big fat dataset that's already sorted
    # index = bin_search(data, poem) (find index of poem with closest similarity score)
    # data.insert(index + 1)
    pass

# searches dataset for similar poem
def binary_search(poems,element,low,high):
     
    # If the lower index of the array exceeds the higher index,
    # that means that the element could not be found in the array.
    if low<=high:
         
        # find the middle index of the array 
        mid=(low+high)//2
 
        #If the middle element is the element we are looking for,
        # return the index of middle element
        if element==arr[mid]:
            print(mid)
         
        # if the element is greater than middle element,
        # search for the element in the second half
        elif element > arr[mid]:
            binary_search(arr,element,mid+1,high)
             
        # if the element is lesser than middle element,
        # search for the element in the first half
        else:
            binary_search(arr,element,low,mid-1) 
         
    else:
        print("Element not found")

def recursive_helper(poems, h,l):

    
    

