from datetime import datetime
import pytz
from typing import Union, Optional

def get_standardized_timestamp(
   timezone: str = "UTC",
   format_string: str = None
) -> Union[datetime, str]:
   """
   Get current timestamp in specified timezone.
   
   Args:
       timezone (str): Target timezone (e.g., "UTC", "America/New_York"). 
                      Defaults to "UTC".
       format_string (str, optional): If provided, returns formatted string.
                                    If None, returns ISO 8601 formatted string
                                    Example: "%Y-%m-%d %H:%M:%S"
   
   Returns:
       Union[datetime, str]: Current timestamp as ISO 8601 string (YYYY-MM-DDThh:mm:ss±hh:mm)
                            or custom formatted string if format_string provided
   
   Raises:
       ValueError: If timezone is invalid or format_string is invalid
   """
   try:
       tz = pytz.timezone(timezone)
       utc_now = datetime.now(pytz.UTC)
       local_time = utc_now.astimezone(tz)
       
       if format_string:
           return local_time.strftime(format_string)
       return local_time.isoformat(timespec='seconds')  # ISO 8601 format
       
   except pytz.exceptions.PytzError as e:
       raise ValueError(f"Invalid timezone: {timezone}. Error: {str(e)}")
   except ValueError as e:
       raise ValueError(f"Invalid format string: {format_string}. Error: {str(e)}")

def convert_to_standard_timestamp(
   timestamp_str: Optional[str],
   timezone: str = "UTC",
   input_format: str = None,
   output_format: str = None
) -> Union[str, None]:
   """
   Convert timestamp string to standardized timestamp in specified timezone.
   
   Args:
       timestamp_str (str, optional): Input timestamp string. 
                                    If None, returns None.
       timezone (str): Target timezone (e.g., "UTC", "America/New_York").
                      Defaults to "UTC".
       input_format (str, optional): Format of input timestamp.
                                   If None, assumes ISO format.
                                   Example: "%Y-%m-%d %H:%M:%S"
       output_format (str, optional): If provided, returns formatted string.
                                    If None, returns ISO 8601 string
   
   Returns:
       Union[str, None]: Converted timestamp as ISO 8601 string (YYYY-MM-DDThh:mm:ss±hh:mm)
                        or None if input is None
   
   Raises:
       ValueError: If timestamp parsing fails, timezone is invalid, or format is invalid
   """
   if timestamp_str is None:
       return None
       
   try:
       # Parse timestamp string based on input format
       if input_format:
           dt = datetime.strptime(timestamp_str, input_format)
           if dt.tzinfo is None:
               dt = pytz.UTC.localize(dt)
       else:
           # Handle ISO format with Z or +00:00
           if timestamp_str.endswith('Z'):
               timestamp_str = timestamp_str[:-1] + '+00:00'
           dt = datetime.fromisoformat(timestamp_str)
           if dt.tzinfo is None:
               dt = pytz.UTC.localize(dt)
       
       # Convert to target timezone
       target_tz = pytz.timezone(timezone)
       converted_dt = dt.astimezone(target_tz)
       
       # Return formatted string if output_format provided
       if output_format:
           return converted_dt.strftime(output_format)
       return converted_dt.isoformat(timespec='seconds')  # ISO 8601 format
       
   except ValueError as e:
       raise ValueError(f"Error parsing timestamp '{timestamp_str}' with format '{input_format}'. Error: {str(e)}")
   except pytz.exceptions.PytzError as e:
       raise ValueError(f"Invalid timezone: {timezone}. Error: {str(e)}")

if __name__ == "__main__":
   # Examples
   try:
       # Get current timestamp in different timezones
       utc_now = get_standardized_timestamp("UTC")
       est_now = get_standardized_timestamp("America/New_York")
       custom_format = get_standardized_timestamp("UTC", "%Y-%m-%d %H:%M:%S")
       
       print(f"Current UTC: {utc_now}")
       print(f"Current EST: {est_now}")
       print(f"Custom format: {custom_format}")
       
       # Convert timestamps
       sample_timestamp = "2024-01-26T10:00:00Z"
       converted_utc = convert_to_standard_timestamp(sample_timestamp, "UTC")
       converted_est = convert_to_standard_timestamp(sample_timestamp, "America/New_York")
       custom_output = convert_to_standard_timestamp(
           sample_timestamp, 
           "UTC",
           output_format="%Y-%m-%d %H:%M:%S %Z"
       )
       
       print(f"\nOriginal: {sample_timestamp}")
       print(f"Converted UTC: {converted_utc}")
       print(f"Converted EST: {converted_est}")
       print(f"Custom output: {custom_output}")
       
   except ValueError as e:
       print(f"Error: {e}")
