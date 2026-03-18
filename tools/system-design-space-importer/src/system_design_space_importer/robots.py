from urllib.parse import urlparse
from urllib.request import urlopen

DEFAULT_USER_AGENT = "system-design-space-importer"


def parse_robots_txt(text, user_agent=DEFAULT_USER_AGENT):
    groups = []
    current_group = None

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue

        field, value = [part.strip() for part in line.split(":", 1)]
        field_lower = field.lower()
        value_lower = value.lower()

        if field_lower == "user-agent":
            if current_group is None or current_group["finalized"]:
                current_group = {
                    "user_agents": [],
                    "crawl_delay_s": None,
                    "disallow_paths": [],
                    "finalized": False,
                }
                groups.append(current_group)
            current_group["user_agents"].append(value_lower)
            continue

        if current_group is None:
            continue

        current_group["finalized"] = True
        if field_lower == "crawl-delay":
            try:
                current_group["crawl_delay_s"] = float(value)
            except ValueError:
                current_group["crawl_delay_s"] = None
        elif field_lower == "disallow" and value:
            current_group["disallow_paths"].append(value)

    requested_user_agent = user_agent.lower()
    matching_group = None
    wildcard_group = None
    for group in groups:
        user_agents = group["user_agents"]
        if requested_user_agent in user_agents:
            matching_group = group
            break
        if "*" in user_agents:
            wildcard_group = group

    selected_group = matching_group or wildcard_group
    if selected_group is None:
        return {
            "user_agent": user_agent,
            "crawl_delay_s": None,
            "disallow_paths": [],
        }

    return {
        "user_agent": user_agent,
        "crawl_delay_s": selected_group["crawl_delay_s"],
        "disallow_paths": selected_group["disallow_paths"],
    }


def build_local_file_robots_policy(user_agent=DEFAULT_USER_AGENT):
    return {
        "status": "not_applicable_local_file",
        "source_url": None,
        "user_agent": user_agent,
        "crawl_delay_s": None,
        "disallow_paths": [],
    }


def fetch_robots_policy(seed, fetch_policy, user_agent=DEFAULT_USER_AGENT):
    parsed_seed = urlparse(seed)
    if parsed_seed.scheme.lower() == "file":
        return build_local_file_robots_policy(user_agent=user_agent)

    hostname = (parsed_seed.hostname or "").lower()
    if hostname not in fetch_policy["allowed_hostnames"]:
        raise ValueError("disallowed discovery host: {0}".format(hostname))

    robots_url = "{0}://{1}/robots.txt".format(parsed_seed.scheme, hostname)
    with urlopen(robots_url, timeout=fetch_policy["timeout_s"]) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        robots_text = response.read().decode(charset, errors="replace")

    parsed_policy = parse_robots_txt(robots_text, user_agent=user_agent)
    return {
        "status": "fetched",
        "source_url": robots_url,
        "user_agent": parsed_policy["user_agent"],
        "crawl_delay_s": parsed_policy["crawl_delay_s"],
        "disallow_paths": parsed_policy["disallow_paths"],
    }
