import java.lang.reflect.Array;
import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;

public class BinaryMinHeap <T extends Comparable<T>> implements MyPriorityQueue<T> {
    private int size; // Maintains the size of the data structure
    private T[] arr; // The array containing all items in the data structure
                     // index 0 must be utilized
    private Map<T, Integer> itemToIndex; // Keeps track of which index of arr holds each item.

    public BinaryMinHeap() {
        // This line just creates an array of type T. We're doing it this way just
        // because of weird java generics stuff (that I frankly don't totally understand)
        // If you want to create a new array anywhere else (e.g. to resize) then
        // You should mimic this line. The second argument is the size of the new array.
        arr = (T[]) Array.newInstance(Comparable.class, 10);
        size = 0;
        itemToIndex = new HashMap<>();
    }

    // helper method to get the parent index
    private int getParent(int i) {
        if (i == 0) {
            return -1;
        }
        return (i - 1) / 2;
    }

    // swap two elements of the 'heap'
    // also updates the hashmap
    private void swap(int i, int j) {
        T temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
        itemToIndex.put(arr[i], i);
        itemToIndex.put(arr[j], j);
    }

    // move the item at index i "rootward" until
    // the heap property holds
    private void percolateUp(int i) {
        // if we have a parent, and we're less than them swap
        // then continue to check until we either don't have parents
        // or we are in the right spot
        int p = getParent(i);
        if (p != -1 && arr[p].compareTo(arr[i]) > 0) {
            swap(i, p);
            percolateUp(p);
        }
    }

    // move the item at index i "leafward" until
    // the heap property holds
    private void percolateDown(int i) {

        // get the index for the left, right nodes
        int l = i * 2 + 1;
        int r = i * 2 + 2;
        int cur_min = i;

        // basically set the cur_min to the minimum value index of the subtree
        // of the given index, and its two child nodes
        if (l < size && arr[l].compareTo(arr[cur_min]) < 0) {
            cur_min = l;
        }

        if (r < size && arr[r].compareTo(arr[cur_min]) < 0) {
            cur_min = r;
        }

        // if we have a child that's less than us (either right or left)
        // swap and continue to bubble down, otherwise we're done
        if (cur_min != i) {
            swap(i, cur_min);
            percolateDown(cur_min);
        }

    }

    // copy all items into a larger array to make more room.
    private void resize(){
        T[] larger = (T[]) Array.newInstance(Comparable.class, arr.length*2);
        for (int i = 0; i < arr.length; i++){
            larger[i] = arr[i];
        }
        arr = larger;
    }

    // O(log n) run time
    public void insert(T item) {
        if (size == arr.length) { // need more space
            resize();
        }
        arr[size] = item;  // add as the rightmost child
        itemToIndex.put(item, size);  // update map
        percolateUp(size);  // check it's in the right spot
        size++;

    }


    public T extract() {
        if (size == 0) {
            throw new IllegalStateException("Heap is empty");
        }
        // save item
        T item = arr[0];

        // put the rightmost child as the new root
        size--;
        arr[0] = arr[size];
        arr[size] = null;
        // update the hashmap
        itemToIndex.put(arr[0], 0);

        itemToIndex.remove(item);

        percolateDown(0);  // adjust its place
        return item;

    }

    // Remove the item at the given index.
    // Make sure to maintain the heap property!
    private T remove(int index) {

        // just swap the item to remove with the root
        // then extract it
        swap(index, 0);
        return extract();

    }

    // We have provided a recommended implementation
    // You're welcome to do something different, though!
    public void remove(T item){

        if (itemToIndex.get(item) == null) {
            throw new IllegalArgumentException("Item is not in the heap");
        } else {
            remove(itemToIndex.get(item));
        }
    }

    // Determine whether to percolate up/down
    // the item at the given index, then do it!
    private void updatePriority(int index) {
        // percolateDown first
        // if we adjusted priority up
        // percolate down should finish quick
        T item = arr[index];
        percolateDown(index);
        // if we didn't go anywhere try going up
        if (itemToIndex.get(item) == index) {
            percolateUp(index);
        }
    }

    // This method gets called after the client has 
    // changed an item in a way that may change its
    // priority. In this case, the client should call
    // updatePriority on that changed item so that 
    // the heap can restore the heap property.
    // Throws an IllegalArgumentException if the given
    // item is not an element of the priority queue.
    // We have provided a recommended implementation
    // You're welcome to do something different, though!
    public void updatePriority(T item){
	    if (!(itemToIndex.containsKey(item))){
            throw new IllegalArgumentException("Given item is not present in the priority queue!");
	    }
        updatePriority(itemToIndex.get(item));
    }

    // We have provided a recommended implementation
    // You're welcome to do something different, though!
    public boolean isEmpty(){
        return size == 0;
    }

    // We have provided a recommended implementation
    // You're welcome to do something different, though!
    public int size(){
        return size;
    }

    // We have provided a recommended implementation
    // You're welcome to do something different, though!
    public T peek(){
        if (isEmpty()) {
            throw new IllegalStateException();
        }
        return arr[0];
    }
    
    // We have provided a recommended implementation
    // You're welcome to do something different, though!
    public List<T> toList(){
        List<T> copy = new ArrayList<>();
        for(int i = 0; i < size; i++){
            copy.add(i, arr[i]);
        }
        return copy;
    }

    // For debugging
    public String toString(){
        if(size == 0) {
            return "[]";
        }
        String str = "[(" + arr[0] + " " + itemToIndex.get(arr[0]) + ")";
        for(int i = 1; i < size; i++ ){
            str += ",(" + arr[i] + " " + itemToIndex.get(arr[i]) + ")";
        }
        return str + "]";
    }
    
}
