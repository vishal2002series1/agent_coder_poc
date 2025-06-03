import requests

def validate_maven_artifact(group_id, artifact_id):
    """
    Checks if the given groupId:artifactId exists in Maven Central.
    Returns the artifact info dict if found, else None.
    """
    url = f"https://search.maven.org/solrsearch/select?q=g:%22{group_id}%22+AND+a:%22{artifact_id}%22&rows=1&wt=json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        docs = resp.json().get("response", {}).get("docs", [])
        if docs:
            return docs[0]  # Contains groupId, artifactId, latestVersion, etc.
        return None
    except Exception as e:
        print(f"Error validating Maven artifact: {e}")
        return None

def get_latest_version(group_id, artifact_id):
    """
    Returns the latest version string for the given groupId:artifactId, or None if not found.
    """
    doc = validate_maven_artifact(group_id, artifact_id)
    if doc:
        return doc.get("latestVersion")
    return None