import time
import threading
import multiprocessing


def calc_square(numbers):
    print("Calculating square numbers")
    for n in numbers:
        time.sleep(0.2)
        print(f"Square: {n*n}")


def calc_cube(numbers):
    print("Calculating cube numbers")
    for n in numbers:
        time.sleep(0.2)
        print(f"Square: {n*n*n}")

if __name__ == "__main__":
    arr = [2, 3, 8, 9]

    t = time.time()
    # calc_square(arr)
    # calc_cube(arr)

    # t1 = threading.Thread(target=calc_square, args=(arr,))
    # t2 = threading.Thread(target=calc_cube, args=(arr,))

    p1 = multiprocessing.Process(target=calc_square, args=(arr,))
    p2 = multiprocessing.Process(target=calc_cube, args=(arr,))

    # t1.start()
    # t2.start()
    #
    # t1.join()
    # t2.join()

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    print(f"Done in: {time.time() - t}")
