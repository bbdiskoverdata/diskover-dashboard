import logging
import csv
import os
from datetime import datetime
from elasticsearch import Elasticsearch
from collections import defaultdict
import humanize
import argparse

# Configure logging (Windows-style timestamp)
logging.basicConfig(
    filename="es_summary.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S"
)

# Connect to Elasticsearch
es = Elasticsearch("http://192.168.1.225:9200")

# Output CSV with Windows-style timestamp
timestamp = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
csv_filename = f"es_summary_{timestamp}.csv"

# Create/open CSV file
csv_file = open(csv_filename, mode='w', newline='', encoding='utf-8')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Index", "Type", "Key", "Count", "Size (Bytes)", "Size (Readable)", "MTime"])

def human_bytes(b):
    return humanize.naturalsize(b, binary=True)

def top_extensions(index):
    logging.info(f"Extracting file extensions by size from 'extension' field for index '{index}'")

    body = {
        "size": 0,
        "query": {
            "term": {
                "type": "file"
            }
        },
        "aggs": {
            "extensions": {
                "terms": {
                    "field": "extension.keyword",  # Make sure 'extension' is mapped as keyword
                    "size": 20,
                    "order": {
                        "total_size": "desc"
                    }
                },
                "aggs": {
                    "total_size": {
                        "sum": {
                            "field": "size"
                        }
                    }
                }
            }
        }
    }

    try:
        res = es.search(index=index, body=body, request_timeout=60)
        buckets = res["aggregations"]["extensions"]["buckets"]
        for bucket in buckets:
            ext = bucket["key"]
            count = bucket["doc_count"]
            size_bytes = int(bucket["total_size"]["value"])
            readable = human_bytes(size_bytes)
            csv_writer.writerow([index, "Top Extension", ext, count, size_bytes, readable, ""])
        logging.info(f"Top extensions written for index '{index}'")
    except Exception as e:
        logging.error(f"Error extracting extensions for index '{index}': {e}")


    try:
        res = es.search(index=index, body=body)
        buckets = res["aggregations"]["extension_from_name"]["buckets"]
        for bucket in buckets:
            ext = bucket["key"]
            count = bucket["doc_count"]
            size_bytes = int(bucket["total_size"]["value"])
            readable = human_bytes(size_bytes)
            csv_writer.writerow([index, "Top Extension", ext, count, size_bytes, readable, ""])
        logging.info(f"Top extensions (sorted by size) written for index '{index}'")
    except Exception as e:
        logging.error(f"Error extracting extensions by size for index '{index}': {e}")


def top_largest_files(index):
    logging.info(f"Querying top 50 largest files for index '{index}'")
    body = {
        "size": 50,
        "query": {
            "bool": {
                "filter": [
                    {"term": {"type": "file"}}
                ]
            }
        },
        "_source": ["name", "size", "mtime"],
        "sort": [{"size": {"order": "desc"}}]
    }

    res = es.search(index=index, body=body)
    for hit in res["hits"]["hits"]:
        source = hit["_source"]
        name = source.get("name", "[no name]")
        size = source.get("size", 0)
        mtime = source.get("mtime", "N/A")
        readable = human_bytes(size)
        csv_writer.writerow([index, "Largest File", name, "", size, readable, mtime])
    logging.info(f"Largest files written for index '{index}'")

def summarize_temperatures(index):
    def summarize(field):
        logging.info(f"Summarizing {field} temperatures for index '{index}'")

        body = {
            "size": 0,
            "query": {
                "term": {
                    "type": "file"
                }
            },
            "aggs": {
                "hot": {
                    "filter": {
                        "range": {
                            field: {
                                "gte": "now-2y"
                            }
                        }
                    },
                    "aggs": {
                        "total_size": {
                            "sum": {
                                "field": "size"
                            }
                        }
                    }
                },
                "warm": {
                    "filter": {
                        "range": {
                            field: {
                                "gte": "now-5y",
                                "lt": "now-2y"
                            }
                        }
                    },
                    "aggs": {
                        "total_size": {
                            "sum": {
                                "field": "size"
                            }
                        }
                    }
                },
                "cold": {
                    "filter": {
                        "range": {
                            field: {
                                "lt": "now-5y"
                            }
                        }
                    },
                    "aggs": {
                        "total_size": {
                            "sum": {
                                "field": "size"
                            }
                        }
                    }
                }
            }
        }

        try:
            res = es.search(index=index, body=body)
            for tier in ["hot", "warm", "cold"]:
                count = res["aggregations"][tier]["doc_count"]
                size = int(res["aggregations"][tier]["total_size"]["value"])
                readable = human_bytes(size)
                csv_writer.writerow([index, f"{field.upper()} Summary", tier, count, size, readable, ""])
            logging.info(f"{field.upper()} summary complete for index '{index}'")
        except Exception as e:
            logging.error(f"Error summarizing {field} for index '{index}': {e}")

    summarize("mtime")
    summarize("atime")



def main(indexes):
    for index in indexes:
        logging.info(f"Processing index: {index}")
        try:
            top_extensions(index)
            top_largest_files(index)
            summarize_temperatures(index)
            logging.info(f"Finished processing index: {index}")
        except Exception as e:
            logging.error(f"Error processing index {index}: {e}")

    csv_file.close()
    logging.info(f"CSV output written to {csv_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("indexes", nargs="+", help="List of index names to query")
    args = parser.parse_args()
    main(args.indexes)
