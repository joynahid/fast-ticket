#!/usr/bin/env python3
"""
Bangladesh Railway Ticket Booking System
Main entry point using the refactored architecture.
"""

import argparse
import asyncio
import logging
from rich.logging import RichHandler
from rich.console import Console
from config import BookingConfig
from application.booking_controller import BookingController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

# Create console for rich output
console = Console()


def main():
    """Main entry point for the railway booking system."""
    parser = argparse.ArgumentParser(description="Book Bangladesh Railway tickets")
    parser.add_argument(
        "--trip", "-t", type=int, default=1, help="Trip number to book (default: 1)"
    )
    parser.add_argument(
        "--refresh",
        "-r",
        action="store_true",
        help="Refresh cache and fetch fresh data",
    )
    parser.add_argument(
        "--from-city", "-f", type=str, help="Source city (overrides config)"
    )
    parser.add_argument(
        "--to-city", "-T", type=str, help="Destination city (overrides config)"
    )
    parser.add_argument(
        "--journey-date",
        "-d",
        type=str,
        help="Journey date in DD-MMM-YYYY format (overrides config)",
    )
    parser.add_argument(
        "--parallel-booking-processes",
        "-p",
        type=int,
        help="Number of parallel booking processes (default: number of CPU cores)",
    )
    parser.add_argument(
        "--infinite-retry",
        "-i",
        action="store_true",
        help="Infinite retry",
    )

    args = parser.parse_args()

    logger = logging.getLogger("main")
    logger.info(f"Starting booking process for trip #{args.trip}")

    # Display journey details
    if args.from_city or args.to_city or args.journey_date:
        logger.info("Using CLI overrides:")
        if args.from_city:
            logger.info(f"From: {args.from_city}")
        if args.to_city:
            logger.info(f"To: {args.to_city}")
        if args.journey_date:
            logger.info(f"Date: {args.journey_date}")

    console.print("=" * 50, style="bold blue")

    # Load configuration
    config = BookingConfig()

    # Initialize controller
    controller = BookingController(config)

    # Run booking process
    while True:
        asyncio.run(
            controller.run_with_retry(
                trip_number=args.trip,
                refresh_cache=True,
                from_city=args.from_city,
                to_city=args.to_city,
                journey_date=args.journey_date,
                parallel_booking_processes=args.parallel_booking_processes,
            )
        )
        if not args.infinite_retry:
            break


if __name__ == "__main__":
    main()
