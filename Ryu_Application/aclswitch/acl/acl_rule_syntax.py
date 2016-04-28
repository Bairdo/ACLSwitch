# Other modules
from netaddr import IPAddress
from netaddr import AddrFormatError

__author__ = "Jarrod N. Bakker"
__status__ = "Development"


class ACLRuleSyntax:
    """A syntax checker for ACL rules. This is used by passing the
    appropriate values into the check_rule() function. The caller
    of check_rule() will be returned a list. If the list is empty
    then the rule is valid. However if the rule is not valid then the
    list will contain the appropriate error messages.
    """

    def check_rule(self, rule):
        """Check if an ACL rule has valid syntax.

        :param rule: ACL rule to perform a syntax check on.
        :return: A list of the error messages. An empty list means
        that all tests passed and the rule is valid.
        """
        ip_src = rule["ip_src"]
        ip_dst = rule["ip_dst"]
        tp_proto = rule["tp_proto"]
        port_src = rule["port_src"]
        port_dst = rule["port_dst"]
        errors = []
        ip_src_result = self.check_ip(ip_src)
        ip_dst_result = self.check_ip(ip_dst)
        if not ip_src_result:
            errors.append("Invalid source IP address: " + ip_src)
        if not ip_dst_result:
            errors.append("Invalid destination IP address: " + ip_dst)
        if ip_src_result and ip_dst_result:
            if not self.check_ip_versions(ip_src, ip_dst):
                errors.append("Unsupported rule: both IP addresses "
                              "must be of the same version.")
        if not self.check_transport_protocol(tp_proto):
            errors.append("Invalid transport protocol (layer 4): " +
                          tp_proto)
        if not self.check_port(port_src):
            errors.append("Invalid source port: " + port_src)
        if not self.check_port(port_dst):
            errors.append("Invalid destination port: " + port_dst)
        if not self.check_transport_valid(tp_proto, port_src, port_dst):
            errors.append("Unsupported rule: transport protocol: " +
                          tp_proto + " source port: " + port_src +
                          " destination port: " + port_dst)
        return errors

    def check_ip(self, address):
        """Check that a valid IP (v4 or v6) address has been specified.

        :param address: The IP address to check.
        :return : True if valid, False if not valid.
        """
        try:
            addr = IPAddress(address)
            return True
        except AddrFormatError:
            if address == "*":
                return True
            return False

    def check_ip_versions(self, ip_src, ip_dst):
        """Check that the source and destination IP addresses are of
        the same version.

        :param ip_src: The source IP address to check.
        :param ip_dst: The destination IP address to check.
        :return: True if valid, False if not valid.
        """
        if ip_src == "*" and ip_dst == "*":
            return False
        if ip_src == "*" or ip_dst == "*":
            return True
        return IPAddress(ip_src).version == IPAddress(ip_dst).version

    def check_transport_protocol(self, protocol):
        """ACLSwtich can block all traffic (denoted by tp_proto ==
        "*") or by checking TCP or UDP port numbers. This function
        checks that the specified transport layer (layer 4) protocol
        is either "*", TCP or UDP.

        :param protocol: The transport layer (layer 4) protocol to check.
        :return: True if valid, False if not valid.
        """
        return (protocol == "tcp" or protocol == "udp" or protocol ==
                "*")

    def check_port(self, port):
        """A port is valid if it is either "*" or between 0 and 65535
        inclusive.

        :param port: The port number to check
        :return: True if valid, False if not valid.
        """
        try:
            int(port)
            if int(port) < 0 or int(port) > 65535:
                return False
            return True
        except ValueError:
            if port == "*":
                return True
            return False

    def check_transport_valid(self, tp_proto, port_src, port_dst):
        """An OFPMatch cannot have both TCP and UDP information in it.
        Therefore an ACL rule is not valid if the tp_proto is "*" and
        port numbers are specified.

        :param tp_proto: The transport layer (layer 4) protocol to check
        :param port_src: The source port to check
        :param port_dst: The destination port to check
        :return: True if valid, False if not valid.
        """
        return not(tp_proto == "*" and (port_src != "*" or port_dst !=
                                        "*"))