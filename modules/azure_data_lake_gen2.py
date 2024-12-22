from azure.storage.filedatalake import DataLakeServiceClient
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

   
class Azure_Data_Lake_Gen2:
    """
        A class to interact with Azure Data Lake Gen2 storage service.
        
        This class allows performing basic operations on a container in Azure Data Lake Gen2,
        such as reading and writing JSON data to a file within the container.
        
        Attributes:
            account_name (str): The Azure Storage account name.
            account_key (str): The Azure Storage account key.
            container_name (str): The name of the container within the Azure Data Lake Gen2 account.
    """

    def __init__(self, account_name, account_key, container_name):
        self.account_name = account_name
        self.account_key = account_key
        self.container_name = container_name

        # Vérification des valeurs
        print(f"Account Name: {self.account_name}")
        print(f"Account Key: {self.account_key}")
        print(f"Container Name: {self.container_name}")

        self.service_client = DataLakeServiceClient(
            account_url=f"https://{self.account_name}.dfs.core.windows.net",
            credential=self.account_key
        ).get_file_system_client(self.container_name)
    
    

    def write_into_container(self,file_path, data):
        """
            Write JSON data into a specified file in the Azure Data Lake Gen2 container.
            
            This method serializes the `data` dictionary into a JSON formatted string and uploads it
            to a specified file path within the Azure Data Lake Gen2 container.
            
            Args:
                service_client (DataLakeServiceClient): The service client used to access the Azure Data Lake.
                file_path (str): The file path in the container where the data will be written.
                data (dict): A dictionary that will be serialized into JSON and uploaded.
            
            Raises:
                Exception: If the upload operation fails, an error message is logged.
        """

        try : 
            json_data = json.dumps(data)
            file_client = self.service_client.get_file_client(file_path)
            file_client.upload_data(json_data, overwrite=True)
            logging.info(f"Dictionary data written to {file_path} successfully.")

        except Exception as e:
            logging.error(f"Failed to write dictionary data to {file_path}: {str(e)}")


    def read_from_container(self,file_path):

        """
            Read JSON data from a specified file in the Azure Data Lake Gen2 container.
            
            This method downloads the contents of a specified file, deserializes the JSON data,
            and returns it as a Python dictionary.
            
            Args:
                service_client (DataLakeServiceClient): The service client used to access the Azure Data Lake.
                file_path (str): The file path in the container from which data will be read.
            
            Returns:
                dict: The dictionary data read from the file, if successful.
            
            Raises:
                Exception: If the read operation fails, an error message is logged.
        """

        try : 
            file_client = self.service_client.get_file_client(file_path)
            file_content = file_client.download_file().readall()
            data = json.loads(file_content.decode("utf-8"))
            logging.info(f"Dictionary data read from {file_path} successfully.")

        except Exception as e:
            logging.error(f"Failed to read dictionary data from {file_path}: {str(e)}")

        return data
    
    def upload_to_container(self, pdf, file_path):

        """
        Upload file data to Azure Data Lake Gen2.

        Args:
            param file_data: Binary content of the file.
            param blob_name: Path and name for the blob in Azure.

        Raises:
            Exception: If the read operation fails, an error message is logged.
        """
        try:


            file_client = self.service_client.get_file_client(file_path)
            file_client.upload_data(pdf, overwrite=True)
            logging.info(f"File uploaded to Azure as {file_path}.")
        except Exception as e:
            logging.error(f"Failed to upload file to Azure: {e}")
            raise
    



