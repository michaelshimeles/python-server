import os
from fastapi import FastAPI, HTTPException
import datetime


class SwipeAction:
    def __init__(self, user_id, station_id, time_stamp):
        self.user_id = user_id
        self.station_id = station_id
        self.time_stamp = time_stamp

    def __str__(self):
        return f"User ID: {self.user_id}, Station ID: {self.station_id}, Time Stamp: {self.time_stamp}"


app = FastAPI()


def write_to_file(filename, data):
    is_empty = os.path.getsize(filename) == 0

    try:
        with open(filename, 'a') as file:
            if is_empty:
                file.write(data)
            else:
                file.write('\n' + data)

        return {
            "status": "Success",
            "message": f"Data written to {filename} successfully."
        }
    except Exception as e:
        return {
            "status": "Failed",
            "message": f"An error occurred: {str(e)}"
        }


def read_file(file_path):
    objects = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            try:
                data = line.strip().split(', ')
                if len(data) >= 3:
                    user_id = data[0].split(': ')[1]
                    station_id = data[1].split(': ')[1]
                    time_stamp_str = data[2].split(': ')[1]

                    time_stamp = datetime.datetime.strptime(
                        time_stamp_str, '%H:%M:%S')

                    swipe_record = SwipeAction(
                        user_id, station_id, str(time_stamp))
                    objects.append(swipe_record)
                else:
                    log_error("error.txt", {
                        "error": "Invalid data format",
                        "time_stamp": datetime.datetime.now()
                    })
                    continue
            except Exception as e:
                log_error("error.txt", {
                    "error": str(e),
                    "time_stamp": datetime.datetime.now()
                })
                continue
    return objects


def log_error(filename, data):
    is_empty = os.path.getsize(filename) == 0
    with open(filename, 'a') as file:
        if is_empty:
            file.write(data)
        else:
            file.write('\n' + data)
    return {
        "status": "Success",
        "message": f"Data written to {filename} successfully."
    }


@app.post("/swipe-in")
async def swipe_in(user_id: str, station_id: str):
    try:
        time = datetime.datetime.now()
        time_stamp = time.strftime("%H:%M:%S")
        data_to_write = f"user_id: {user_id}, station_id: {station_id}, time_stamp: {time_stamp}"
        swipe_in_record = write_to_file(
            "swipe-in.txt", data_to_write)

        if swipe_in_record["status"] == "Failed":
            log_error("error.txt", {
                "error": swipe_in_record["message"],
                "timestamp": time_stamp
            })
            return "Failed"
        return {"Result": swipe_in_record}
    except Exception as e:

        log_error("error.txt", {
            "error": str(e),
            "time_stamp": datetime.datetime.now()
        })
        return HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/swipe-out")
async def swipe_out(user_id: str, station_id: str):
    try:
        time = datetime.datetime.now()
        time_stamp = time.strftime("%H:%M:%S")
        data_to_write = f"user_id: {user_id}, station_id: {station_id}, time_stamp: {time_stamp}"
        swipe_in_record = write_to_file("swipe-out.txt", data_to_write)

        if swipe_in_record["status"] == "Failed":
            log_error("error.txt", {
                "error": swipe_in_record["message"],
                "timestamp": time_stamp
            })
            return "Failed"
        return {"Result": swipe_in_record}
    except Exception as e:
        time = datetime.datetime.now()
        time_stamp = time.strftime("%H:%M:%S")

        log_error("error.txt", {
            "error": str(e),
            "time_stamp": time_stamp
        })
        return HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/average-time/{start_station_id}/{end_station_id}")
async def calculate_average_time(start_station_id: str, end_station_id: str):
    try:
        swipe_in_records = read_file("swipe-in.txt")
        swipe_out_records = read_file("swipe-out.txt")

        filtered_swipe_in_records = [
            record for record in swipe_in_records if record.station_id == start_station_id]
        filtered_swipe_out_records = [
            record for record in swipe_out_records if record.station_id == end_station_id]

        if not filtered_swipe_in_records or not filtered_swipe_out_records:
            return {"average_time": "N/A"}

        total_time = datetime.timedelta()

        for swipe_in_record in filtered_swipe_in_records:
            matching_swipe_out_record = next(
                (record for record in filtered_swipe_out_records if record.user_id ==
                 swipe_in_record.user_id),
                None
            )

            if matching_swipe_out_record:
                total_time += datetime.datetime.strptime(matching_swipe_out_record.time_stamp, "%Y-%m-%d %H:%M:%S") - \
                    datetime.datetime.strptime(
                        swipe_in_record.time_stamp, "%Y-%m-%d %H:%M:%S")

        average_time = total_time / len(filtered_swipe_in_records)

        return {"average_time": str(average_time)}

    except Exception as e:
        time = datetime.datetime.now()
        time_stamp = time.strftime("%H:%M:%S")
        log_error("error.txt", {
            "error": str(e),
            "time_stamp": time_stamp
        })
        return HTTPException(status_code=500, detail="Internal Server Error")
